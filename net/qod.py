"""CAMARA Quality on Demand (QoD) istemcisi.

Saglayici-bagimsiz: Turkcell uc noktalari geldiginde yalnizca base_url/token degisir.
mock=True iken sebeke yerine yerel benzetim kullanilir; tum durum makinesi ve olcum
duzenegi kimlik bilgileri gelmeden calisir (bkz. docs/5g-entegrasyon-plani.md).
"""
import json
import time
import urllib.error
import urllib.request

# CAMARA qosStatus degerleri
REQUESTED = 'REQUESTED'
AVAILABLE = 'AVAILABLE'
UNAVAILABLE = 'UNAVAILABLE'


class QoDError(Exception):
    """QoD API hatasi (HTTP kodu ve CAMARA hata kodu ile birlikte)."""

    def __init__(self, status, code, message):
        super().__init__(f'{status} {code}: {message}')
        self.status, self.code, self.message = status, code, message


class QoDClient:
    """CAMARA QoD /sessions adaptoru.

    Gercek modda 3 uc nokta kullanilir: POST /sessions, GET /sessions/{id},
    DELETE /sessions/{id}. Kalite garantisi POST yanitiyla degil qosStatus'un
    AVAILABLE olmasiyla baslar -> wait_available() bunun icindir.
    """

    def __init__(self, base_url=None, token=None, mock=False,
                 mock_setup_seconds=1.2, timeout=10.0):
        self.base_url = (base_url or '').rstrip('/')
        self.token = token
        self.mock = mock or not self.base_url
        self.timeout = timeout
        self._mock_setup = mock_setup_seconds
        self._mock_sessions = {}
        self.session_id = None

    # ------------------------------------------------------------------ HTTP
    def _request(self, method, path, body=None):
        url = self.base_url + path
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header('Content-Type', 'application/json')
        if self.token:
            req.add_header('Authorization', 'Bearer ' + self.token)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                raw = r.read().decode() or '{}'
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            detail = {}
            try:
                detail = json.loads(e.read().decode() or '{}')
            except Exception:
                pass
            raise QoDError(e.code, detail.get('code', ''), detail.get('message', str(e)))

    # --------------------------------------------------------------- islemler
    def create_session(self, qos_profile='QOS_L', duration=30, device=None,
                       application_server=None, device_ports=None,
                       application_server_ports=None, sink=None):
        """POST /sessions -> sessionId. device: {'phoneNumber': '+90...'} vb."""
        body = {'duration': int(duration), 'qosProfile': qos_profile}
        # applicationServer CAMARA'da zorunlu; mock'ta sembolik deger yeter.
        body['applicationServer'] = application_server or {'ipv4Address': '203.0.113.10/32'}
        if device:
            body['device'] = device
        if device_ports:
            body['devicePorts'] = device_ports
        if application_server_ports:
            body['applicationServerPorts'] = application_server_ports
        if sink:
            body['sink'] = sink

        if self.mock:
            sid = 'mock-%d' % int(time.time() * 1000)
            self._mock_sessions[sid] = {
                'sessionId': sid, 'duration': int(duration), 'qosProfile': qos_profile,
                'applicationServer': body['applicationServer'],
                'requestedAt': time.time(),
            }
        else:
            info = self._request('POST', '/sessions', body)
            sid = info['sessionId']
        self.session_id = sid
        return sid

    def get_session(self, session_id=None):
        """GET /sessions/{id} -> SessionInfo (qosStatus dahil)."""
        sid = session_id or self.session_id
        if not sid:
            return None
        if self.mock:
            s = self._mock_sessions.get(sid)
            if not s:
                raise QoDError(404, 'NOT_FOUND', 'oturum yok')
            elapsed = time.time() - s['requestedAt']
            if elapsed < self._mock_setup:
                status = REQUESTED          # sebeke kaynagi henuz tahsis etmedi
            elif elapsed < self._mock_setup + s['duration']:
                status = AVAILABLE
            else:
                status = UNAVAILABLE
            out = dict(s, qosStatus=status)
            if status != REQUESTED:
                out['startedAt'] = s['requestedAt'] + self._mock_setup
            return out
        return self._request('GET', '/sessions/' + sid)

    def wait_available(self, session_id=None, timeout=8.0, poll=0.25):
        """qosStatus AVAILABLE olana kadar bekler. Kaliteyi buna gore yukselt."""
        sid = session_id or self.session_id
        deadline = time.time() + timeout
        while time.time() < deadline:
            info = self.get_session(sid)
            status = (info or {}).get('qosStatus')
            if status == AVAILABLE:
                return True
            if status == UNAVAILABLE:
                return False
            time.sleep(poll)
        return False

    def extend_session(self, extra_seconds, session_id=None):
        """POST /sessions/{id}/extend — pencere yetmezse uzat."""
        sid = session_id or self.session_id
        if self.mock:
            s = self._mock_sessions.get(sid)
            if s:
                s['duration'] += int(extra_seconds)
            return True
        self._request('POST', '/sessions/%s/extend' % sid,
                      {'requestedAdditionalDuration': int(extra_seconds)})
        return True

    def delete_session(self, session_id=None):
        """DELETE /sessions/{id} — pencere bitince kaynagi sebekeye iade et."""
        sid = session_id or self.session_id
        if not sid:
            return False
        try:
            if self.mock:
                self._mock_sessions.pop(sid, None)
            else:
                self._request('DELETE', '/sessions/' + sid)
        except QoDError as e:
            if e.status != 404:
                raise
        finally:
            if sid == self.session_id:
                self.session_id = None
        return True
