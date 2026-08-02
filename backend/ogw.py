"""Turkcell Open Gateway istemcisi — Number Verification + Quality on Demand.

Akis BACKEND MERKEZLIDIR: client_id/secret burada durur, mobil uygulamada DEGIL.
(Sartname: "Open Gateway Demo - UX Akis Kilavuzu")

NV akisi:
  1) App -> /nv/basla  : backend authorize URL'i uretir
  2) Cihaz (HUCRESEL AGDA) -> OGW /oauth2/authorize -> 302 -> /api/auth/callback?code=
  3) Backend -> /oauth2/token  (Basic Auth: base64(client_id:client_secret))
  4) Backend -> /number-verification/v1/verify  {"phoneNumber": "+90..."}
     -> {"devicePhoneNumberVerified": true}

QoD:
  POST /quality-on-demand/v1/sessions
  {"duration":60,"applicationServer":{"ipv4Address":"0.0.0.0/0"},"qosProfile":"teknofest2026"}
  -> 201 Created = BASARILI

NOT: Turkcell dagitiminda QoD'de yalniz POST /sessions vardir (GET/DELETE/extend YOK),
basari yalnizca 201 ile belirlenir. Jeton omru 300 sn'dir.
"""
import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid

SCOPE = ('openid '
         'dpv:RequestedServiceProvision#quality-on-demand:sessions:create '
         'dpv:FraudPreventionAndDetection#number-verification:verify')


class OgwConfig:
    """Kimlik bilgileri 3 Agustos toplantisinda gelecek -> hepsi env'den okunur."""

    def __init__(self):
        self.api = os.environ.get('OGW_API_URL', '').rstrip('/')
        self.client_id = os.environ.get('OGW_CLIENT_ID', '')
        self.client_secret = os.environ.get('OGW_CLIENT_SECRET', '')
        self.redirect_uri = os.environ.get(
            'OGW_REDIRECT_URI', 'http://8.234.235.53:8080/api/auth/callback')
        self.qos_profile = os.environ.get('OGW_QOS_PROFILE', 'teknofest2026')

    @property
    def hazir(self):
        return bool(self.api and self.client_id and self.client_secret)

    def __repr__(self):
        return 'OgwConfig(api=%s, client_id=%s, hazir=%s)' % (
            self.api or '-', (self.client_id[:6] + '...') if self.client_id else '-',
            self.hazir)


class OgwHata(Exception):
    def __init__(self, adim, status, govde):
        super().__init__('%s basarisiz (HTTP %s): %s' % (adim, status, govde))
        self.adim, self.status, self.govde = adim, status, govde


class OgwClient:
    def __init__(self, cfg=None, mock=None, timeout=15.0):
        self.cfg = cfg or OgwConfig()
        # Kimlik bilgisi yoksa otomatik mock: gelistirme kimlik bilgisi beklemesin.
        self.mock = (not self.cfg.hazir) if mock is None else mock
        self.timeout = timeout

    # ------------------------------------------------------------------ HTTP
    def _istek(self, adim, url, veri=None, basliklar=None, form=False):
        govde = None
        basliklar = dict(basliklar or {})
        if veri is not None:
            if form:
                govde = urllib.parse.urlencode(veri).encode()
                basliklar['Content-Type'] = 'application/x-www-form-urlencoded'
            else:
                govde = json.dumps(veri).encode()
                basliklar['Content-Type'] = 'application/json'
        req = urllib.request.Request(url, data=govde, headers=basliklar,
                                     method='POST' if veri is not None else 'GET')
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                ham = r.read().decode() or '{}'
                return r.status, (json.loads(ham) if ham.strip().startswith('{') else ham)
        except urllib.error.HTTPError as e:
            try:
                detay = e.read().decode()
            except Exception:
                detay = str(e)
            raise OgwHata(adim, e.code, detay)

    def _temel_yetki(self):
        cift = '%s:%s' % (self.cfg.client_id, self.cfg.client_secret)
        return 'Basic ' + base64.b64encode(cift.encode()).decode()

    # ---------------------------------------------------- Number Verification
    def authorize_url(self, state=None):
        """Cihazin (hucresel agda) acacagi yetkilendirme adresi."""
        state = state or uuid.uuid4().hex
        q = urllib.parse.urlencode({
            'response_type': 'code',
            'client_id': self.cfg.client_id,
            'redirect_uri': self.cfg.redirect_uri,
            'scope': SCOPE,
            'state': state,
        })
        return '%s/oauth2/authorize?%s' % (self.cfg.api, q), state

    def token_al(self, code):
        """Yetkilendirme kodunu erisim jetonuyla takas eder (Basic Auth)."""
        if self.mock:
            return 'mock-token'
        _, govde = self._istek('token', self.cfg.api + '/oauth2/token',
                               veri={'grant_type': 'authorization_code',
                                     'code': code,
                                     'redirect_uri': self.cfg.redirect_uri},
                               basliklar={'Authorization': self._temel_yetki()},
                               form=True)
        jeton = (govde or {}).get('access_token')
        if not jeton:
            raise OgwHata('token', 200, 'access_token yok: %s' % govde)
        return jeton

    def numara_dogrula(self, telefon, jeton):
        """POST /number-verification/v1/verify -> devicePhoneNumberVerified."""
        if self.mock:
            return True, {'devicePhoneNumberVerified': True, 'mock': True}
        _, govde = self._istek(
            'number-verification',
            self.cfg.api + '/number-verification/v1/verify',
            veri={'phoneNumber': telefon},
            basliklar={'Authorization': 'Bearer ' + jeton})
        return bool((govde or {}).get('devicePhoneNumberVerified')), govde

    # ------------------------------------------------------ Quality on Demand
    def qod_oturum(self, sure=60, jeton=None):
        """POST /quality-on-demand/v1/sessions -> 201 Created = BASARILI."""
        govde_istek = {
            'duration': int(sure),
            'applicationServer': {'ipv4Address': '0.0.0.0/0'},
            'qosProfile': self.cfg.qos_profile,
        }
        if self.mock:
            return True, {'sessionId': 'mock-' + uuid.uuid4().hex[:8], 'mock': True}
        basliklar = {'Authorization': 'Bearer ' + jeton} if jeton else {}
        status, govde = self._istek('quality-on-demand',
                                    self.cfg.api + '/quality-on-demand/v1/sessions',
                                    veri=govde_istek, basliklar=basliklar)
        return status == 201, govde
