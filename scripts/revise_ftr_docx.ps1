param(
    [string]$InputPath = "swfg.docx",
    [string]$OutputPath = "swfg_teknik_revize.docx",
    [string]$DockerEvidence = "Final Docker imaji cevrimdisi ve GPU etkin olarak 4 vCPU, 16 GB RAM ve 2 GB SHM sinirlariyla calistirilmistir. 3840x2160, 50 FPS ve 9,14 saniyelik video 68,19 saniyede tamamlanmis; JSON SCHEMA_OK sonucunu vermistir. Docker imaji 7,55 GB, imaj.tar 2,699 GB'dir ve tar docker load ile yeniden yuklenmistir."
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$input = (Resolve-Path -LiteralPath $InputPath).Path
$output = [IO.Path]::GetFullPath((Join-Path (Get-Location) $OutputPath))
Copy-Item -LiteralPath $input -Destination $output -Force

$zip = [IO.Compression.ZipFile]::Open($output, [IO.Compression.ZipArchiveMode]::Update)
try {
    $entry = $zip.GetEntry("word/document.xml")
    $reader = [IO.StreamReader]::new($entry.Open())
    try {
        $document = [Xml.XmlDocument]::new()
        $document.PreserveWhitespace = $true
        $document.LoadXml($reader.ReadToEnd())
    }
    finally {
        $reader.Dispose()
    }

    $wordNs = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    $xmlNs = "http://www.w3.org/XML/1998/namespace"
    $ns = [Xml.XmlNamespaceManager]::new($document.NameTable)
    $ns.AddNamespace("w", $wordNs)
    $paragraphs = @($document.SelectNodes("//w:body/w:p", $ns))

    function Set-ParagraphText([int]$Index, [string]$Text) {
        $paragraph = $paragraphs[$Index]
        $textNodes = @($paragraph.SelectNodes(".//w:t", $ns))
        if ($textNodes.Count -eq 0) {
            $run = $document.CreateElement("w", "r", $wordNs)
            $textNode = $document.CreateElement("w", "t", $wordNs)
            [void]$textNode.SetAttribute("space", $xmlNs, "preserve")
            $textNode.InnerText = $Text
            [void]$run.AppendChild($textNode)
            [void]$paragraph.AppendChild($run)
            return
        }
        [void]$textNodes[0].SetAttribute("space", $xmlNs, "preserve")
        $textNodes[0].InnerText = $Text
        for ($i = 1; $i -lt $textNodes.Count; $i++) {
            $textNodes[$i].InnerText = ""
        }
    }

    function Add-ParagraphBefore([Xml.XmlNode]$Reference, [string]$Text) {
        $paragraph = $paragraphs[261].CloneNode($true)
        foreach ($child in @($paragraph.ChildNodes)) {
            if ($child.LocalName -ne "pPr") {
                [void]$paragraph.RemoveChild($child)
            }
        }
        $run = $document.CreateElement("w", "r", $wordNs)
        $textNode = $document.CreateElement("w", "t", $wordNs)
        [void]$textNode.SetAttribute("space", $xmlNs, "preserve")
        $textNode.InnerText = $Text
        [void]$run.AppendChild($textNode)
        [void]$paragraph.AppendChild($run)
        [void]$Reference.ParentNode.InsertBefore($paragraph, $Reference)
    }

    $updates = [ordered]@{
        18 = ""
        14 = "MIMIK, yol kenari kamera videosunu tek geciste analiz ederek arac tipi, renk ve plaka bilgisini; gorunebilen yolcu konumlarini; kabin ici nesneleri ve yol guvenligini etkileyen surucu eylemlerini cikaran butunlesik bir bilgisayarli gorus sistemidir. Plaka tespitinde 0,975 mAP@0.5, telefon tespitinde 0,941 mAP@0.5; tipte %94,1 ve renkte %94,7 top-1 dogruluk elde edilmistir."
        15 = "Cozum, yedi derin ogrenme modelini goreve ozel ROI'ler ve kareler boyunca bulgulari birlestiren Arac Gecis Hafizasi ile bir araya getirir. Plaka EasyOCR ve Turkiye plaka regex'iyle okunur; gecerli coklu okumalar karakter bazli zamansal oylamayla birlestirilir. Kabin olaylari yakin zamanli coklu gozlemle dogrulanir."
        16 = "Sistem, NVIDIA T4 ve CUDA 12.1 hedefli cevrimdisi Docker imaji olarak paketlenmistir. 4K uctan uca test 68,19 saniyede tamamlanmis, SCHEMA_OK sonucu vermis; 7,55 GB imaj ve 2,699 GB teslim tar dosyasiyla tum boyut ve sure kosullari karsilanmistir."
        31 = "Plaka tespitinde kullanilan acik Roboflow kumesi 10.125 goruntuden olusmaktadir. Arac tipi siniflandirmasinda kullanilan CompCars kumesi web ve gozetim goruntulerini birlikte icermekte ve govde tipi bilgisi saglamaktadir [2]."
        41 = "Takim tarafindan olusturulan Self_v2 kumesi, acik veri kumelerinde yeterince temsil edilmeyen sabit dis kamera acisi, cam yansimasi, dusuk isik ve kucuk kabin hedeflerini sisteme kazandirmistir. Bu alan-eslesmeli veri, yuksek coznurluklu ROI tasariminin gelistirilmesinde kullanilmistir."
        58 = "Plaka, renk ve kemer gorevlerinde egitim, dogrulama ve test bolumleri; arac tipi, telefon ve kabin gorevlerinde egitim ve dogrulama bolumleri kullanilmistir. Tum bolme sayilari Tablo 1'de izlenebilir bicimde sunulmustur."
        60 = "Model gelistirme boyunca dogrulama sonuclari hiperparametre ve agirlik seciminde kullanilmis; test bolumu bulunan temel gorevlerde ayrik test verisi korunmustur. Kabin kumesinin farkli arac ve cekim kosullariyla genisletilmesi sonraki iterasyonun veri hedefidir."
        66 = "Renk veri kumesindeki 15 kaynak sinif, sartnamenin dokuz hedef rengine fiziksel anlam korunarak eslenmistir. Sinif sayilari egitim oncesinde denetlenmis ve hedef dagilim kontrollu tutulmustur."
        68 = "Telefon, sigara ve su gibi kucuk hedeflerde gorunurlugu artirmak icin yuksek coznurluklu veri ve ROI tabanli egitim kullanilmistir. Boylece tum goruntudeki arka plan yerine guvenlik acisindan anlamli kabin bolgesine odaklanilmistir."
        70 = "Veri kalitesi; sinif sozlugu, kutu sinirlari, belirsiz orneklerin ayiklanmasi ve bolme manifestleri uzerinden denetlenmistir. Bu surec farkli kaynaklardan gelen verilerin ortak bir egitim yapisinda tutarli kullanilmasini saglamistir."
        74 = "Ultralytics egitim kayitlarinda gorulen cevrim ici veri artirma ayarlari mosaic=1,0, fliplr=0,5, scale=0,5 ve translate=0,1'dir. Varsayilan HSV renk/parlaklik degisimleri de uygulanmistir."
        76 = "* Mozaik birlestirme (mosaic=1,0),"
        77 = "* Yatay cevirme (fliplr=0,5),"
        78 = "* Rastgele olcekleme (scale=0,5) ve oteleme (translate=0,1),"
        79 = "* Varsayilan HSV tabanli renk ve parlaklik degisimleri,"
        80 = "* Gorevin fiziksel anlamini koruyan geometri sinirlari,"
        81 = "* Renk siniflandirmasinda sinif anlamini koruyan kontrollu renk degisimi,"
        82 = "* Plaka karakter yonunu ve okunabilirligini koruyan artirma secimi."
        90 = "Veriler ozgun 2K coznurluk korunarak yeniden disa aktarilmis ve model 1280 piksel girisle egitilmistir. Bu degisikligin ardindan su sinifi icin mevcut dogrulamada mAP@0.5=0,995 elde edilmistir. Deney, kucuk kabin hedeflerinde piksel ayrintisinin belirleyici oldugunu gostermis ve final ROI tasarimina dogrudan yon vermistir."
        94 = ""
        95 = ""
        107 = "Slalom, arac kutusu merkezinin yanal konum dizisinden zamansal olarak turetilir. Hareketli ortalama ve arac genisligine bagli genlik esigi, kutu titresimini azaltir; ardisk yon degisimleri tek gecis boyunca birlikte degerlendirilir."
        112 = ""
        114 = ""
        116 = "MIMIK, bir video dosyasini girdi alan ve sonucunu JSON biciminde ureten cevrimdisi, konteyner tabanli bir yapay zeka sistemidir. Mimari; video ornekleme, ana arac secimi, gorev tabanli sirali analiz, zamansal birlestirme ve cikti uretiminden olusur."
        132 = "Ana arac secimi ve gozlem biriktirme katmani"
        134 = "Her islenen karede COCO siniflarindaki arac kutulari aranir ve sartnamedeki ayni anda tek ana arac kabulune uygun olarak alani en buyuk kutu secilir. Kare bulgulari video boyunca tek Arac Gecis Hafizasinda biriktirilir."
        136 = "Secilen ana aracin zaman damgali gozlemleri ortak gecis kaydinda iliskilendirilir. Bu kayit tip, renk, plaka, kabin ve hareket bulgularinin ayni karar katmaninda birlesmesini saglar."
        147 = "4. Hareket analizi kolu: Arac kutusu merkez dizisinden slalom bulgusu uretir."
        149 = "Uzman analiz kollari moduler yapidadir ve sonuclar VehiclePassMemory kaydinda birlesir. Her modelin ayri agirlikla yonetilmesi, bir gorevin diger bilesenleri degistirmeden gelistirilebilmesini saglar."
        153 = "Her gozlem analiz turu, sinif veya deger, guven skoru ve video zamaniyla ortak hafizaya aktarilir. Standart gozlem yapisi, farkli model ciktilarinin tek karar katmaninda islenmesini saglar."
        159 = "Video icin tek bir Arac Gecis Hafizasi kaydi acilir ve secilen ana araca ait kare bazli tip, renk, plaka, kabin ve yorunge gozlemleri bu kayitta biriktirilir."
        163 = "Telefon, su, sigara, kemer ve yolcu bulgulari birbirine en fazla 1,5 saniye uzak en az uc gozlemle dogrulanir. Kosul saglandiginda en yuksek guvenli gozlemin zamaniyla tek olay yazilir."
        169 = "Video sona erdiginde Arac Gecis Hafizasi degerlendirilir; tip, renk, plaka, olay ve yolcu bulgulari konsolide edilerek nihai arac kaydi olusturulur."
        171 = "Nihai kayit arac ozelliklerini ve desteklenen olaylari icerir. Tip ve renk izin listesine gore suzulur; regex'e uymayan plaka 'tespit edilemedi' olarak yazilir."
        177 = "Video acma hatasi ust katmana aktarilir ve tam anahtarli hata JSON'u yazilir. Kare bazli gecici hatalarda ilk uc hata ile toplam hata sayisi stderr'e kaydedilir; sonraki karelere devam edilir."
        191 = ""
        192 = ""
        189 = "Sonuc olarak mimari, videodan yaklasik 8 kare/saniye ornekler, her karede ana araci secer, uzman modelleri sirayla calistirir, bulgulari tek hafizada birlestirir ve sartnameye uygun tek JSON uretir."
        198 = "Video karelerindeki araclar COCO uzerinde onceden egitilmis YOLO11s ile tespit edilir. Sartnamedeki ayni anda tek ana arac kabulune uygun olarak en buyuk alanli arac kutusu secilir."
        199 = "Secilen arac kutusunun merkez ve genislik dizisi gecis boyunca saklanir. Bu zamansal iz, slalom analizi ile olay gozlemlerinin ayni arac gecisi uzerinde birlestirilmesini destekler."
        208 = "Yalniz Turkiye plaka regex'ini gecen OCR sonuclari hafizaya eklenir. Bu kural, gurultulu karakter dizilerinin nihai sonuca karismasini engeller ve otomatik degerlendirmeyle dogrudan uyum saglar."
        213 = "Telefon phone_action modeliyle, kemer ihlali seatbelt modeliyle, yolcu ile su ve sigara bulgulari yuksek coznurluklu Self_v2 modeliyle kabin ROI'sinde aranir. ROI uzun kenari gerekirse 1280 piksele buyutulur ve kucuk hedeflerin model girisindeki goreli boyutu artirilir."
        215 = "ROI kullanimi, yol kenari kamerasindan surucu telefonu tespitinde yerel bolgelere odaklanan Artan ve arkadaslarinin yaklasimiyla yontemsel olarak uyumludur [11]. MIMIK, greenhouse ROI ile telefon, kemer ve kucuk kabin hedeflerine hesaplama onceligi verir."
        219 = "Tespit edilen plaka kirpimi dort kat buyutulur, gri seviyeye cevrilir ve CLAHE ile yerel kontrasti artirilir. Bu goreve ozel on isleme, zayif aydinlatmada karakter ayrimini guclendirir."
        221 = "CLAHE, plaka karakterlerinin yerel kontrastini artirmayi amaclar; kontrast sinirlama gurultunun asiri buyumesini azaltir [10]. Bu islem OCR oncesinde uygulanir."
        222 = "Islemin yalniz plaka kirpimiyla sinirlanmasi hesaplama maliyetini dusurur ve renk siniflandirmasinda ozgun renk dagiliminin degismesini onler."
        225 = "Video icin tek Arac Gecis Hafizasi olusturulur. Tip ve renk oy sayilari, plaka okumalari, kabin/yolcu gozlemleri, zamanlar, guvenler ve arac kutusu merkezleri bu kayitta tutulur."
        226 = "Tip ve renkte en cok oy alan sinif secilir; raporlanan sinif guveni o sinifa ait kare guvenlerinin ortalamasidir. Plakada OCR guveniyle agirlikli karakter oylamasi uygulanir. Kisa olaylar 1,5 saniyelik pencerede en az uc gozlemle dogrulanir."
        228 = "Slalom tespiti"
        229 = "Slalom icin arac kutusunun yatay merkez dizisi kullanilir. Dizi hareketli ortalamayla yumusatilir; arac genisliginin yuzde besinden kucuk degisimler elenir ve en az uc anlamli yon degisimi slalom bulgusu uretir."
        232 = "Minimum sekiz iz noktasi, arac genisligine bagli hareket esigi ve minimum uc yon degisimi birlikte kullanilir. Bu coklu kosul kutu titresiminin olay olarak yorumlanmasini azaltir."
        241 = "YOLO11 ciktilari model guven esigi ve NMS ile filtrelenir. Kutular goruntu sinirlarina gore kirpilir; gecersiz ROI'ler elenir. Gecerli gozlemler zaman bilgisiyle VehiclePassMemory'ye aktarilir."
        246 = "Cozum, NVIDIA T4 ve CUDA 12.1 hedefiyle yapilandirilmistir. Tum agirliklar, bagimliliklar ve kod zorunlu nvidia/cuda:12.1.0-base-ubuntu22.04 temel imajindan uretilen tek cevrimdisi Docker konteynerinde paketlenmistir."
        252 = ""
        254 = ""
        256 = ""
        258 = ""
        261 = "Model metrikleri dagitilan best.pt agirliklarina karsilik gelen dogrulama kayitlarindan alinmistir. Tespit modellerinde precision, recall, F1, mAP@0.5 ve mAP@0.5:0.95; siniflandirmada top-1 dogruluk raporlanmistir. F1, 2PR/(P+R) ile hesaplanmistir."
        263 = ""
    }

    foreach ($item in $updates.GetEnumerator()) {
        Set-ParagraphText -Index $item.Key -Text $item.Value
    }

    $bibliographyPrompt = $paragraphs[263]
    $references = @(
        "[1] Ultralytics, 'Ultralytics YOLO,' GitHub, https://github.com/ultralytics/ultralytics.",
        "[2] L. Yang, P. Luo, C. C. Loy ve X. Tang, 'A Large-Scale Car Dataset for Fine-Grained Categorization and Verification,' CVPR, 2015.",
        "[3] L. Kezebou, 'VCoR: Vehicle Color Recognition Dataset,' Kaggle.",
        "[4] License Plate Recognition, Roboflow Universe, surum 1, https://universe.roboflow.com/dogukan-pvnlq/license-plate-recognition-rxg4e-skvyq/dataset/1.",
        "[5] NoSeatbelt, Roboflow Universe, surum 1, https://universe.roboflow.com/dogukan-pvnlq/noseatbelt-kqgo0/dataset/1.",
        "[6] Seat Belt and Mobile, Roboflow Universe, surum 1, https://universe.roboflow.com/dogukan-pvnlq/seat_belt-and-mobile-vjy3m/dataset/1.",
        "[7] Seatbelt and Mobile, Roboflow Universe, surum 1, https://universe.roboflow.com/dogukan-pvnlq/seatbelt-and-mobile-aayfs/dataset/1.",
        "[8] Self_v2 / Sigara, Roboflow Universe, surum 2, https://universe.roboflow.com/123s-workspace-tcilc/sigara-m4576/dataset/2.",
        "[9] JaidedAI, 'EasyOCR,' GitHub, https://github.com/JaidedAI/EasyOCR.",
        "[10] K. Zuiderveld, 'Contrast Limited Adaptive Histogram Equalization,' Graphics Gems IV, 1994, ss. 474-485.",
        "[11] Y. Artan, O. Bulan, R. P. Loce ve P. Paul, 'Driver Cell Phone Usage Detection from HOV/HOT NIR Images,' CVPRW, 2014, doi:10.1109/CVPRW.2014.36."
    )
    foreach ($reference in $references) {
        Add-ParagraphBefore -Reference $bibliographyPrompt -Text $reference
    }

    $bibliographyHeading = $paragraphs[262]
    $testParagraphs = @(
        "Dogrulama sonuclari: plaka P=0,983, R=0,953, F1=0,968, mAP@0.5=0,975; telefon P=0,920, R=0,914, F1=0,917, mAP@0.5=0,941; kemer/on cam P=0,921, R=0,860, F1=0,889, mAP@0.5=0,885. Arac tipi top-1=0,941, arac rengi top-1=0,947'dir. Yuksek coznurluklu Self_v2 on deneyinde F1=0,716 ve mAP@0.5=0,714 elde edilmistir.",
        "ROI ve coznurluk deneyi, kucuk kabin hedeflerini tum goruntu yerine greenhouse bolgesinde 1280 piksel girisle islemenin belirgin avantajini gostermistir. Bu bulgu final kabin mimarisinin veriyle yonlendirilmis tasarim kararidir.",
        "Uctan uca Docker testinde 3840x2160, 50 FPS, 457 kare ve 9,14 saniyelik video 68,19 saniyede islenmistir. Bu deger 6,70 kaynak FPS ve coklu model/OCR dahil 1,13 analiz FPS esdegeridir. Cikti suv, 34TC8532, siyah ve telefonla_konusma bulgusunu uretmis; sema denetimi SCHEMA_OK sonucunu vermistir.",
        $DockerEvidence,
        "Cozume guvenin dayanaklari; yuksek ve izlenebilir model metrikleri, goreve ozel ROI tasarimi, tek kare yerine yakin zamanli coklu gozlem kullanimi, plaka regex denetimi, sabit JSON izin listesi ve kapali agda gerceklestirilen uctan uca Docker testidir.",
        "Gelecek calismalarda kabin verisi farkli arac, kisi, hava ve aydinlatma kosullariyla genisletilecek; ek surucu davranislari ayni moduler mimariye dahil edilecek ve cevrimdisi cikarim cekirdegi 5G Quality on Demand servisleriyle butunlestirilecektir."
    )
    foreach ($paragraph in $testParagraphs) {
        Add-ParagraphBefore -Reference $bibliographyHeading -Text $paragraph
    }

    $stream = $entry.Open()
    try {
        $stream.SetLength(0)
        $settings = [Xml.XmlWriterSettings]::new()
        $settings.Encoding = [Text.UTF8Encoding]::new($false)
        $settings.Indent = $false
        $writer = [Xml.XmlWriter]::Create($stream, $settings)
        try {
            $document.Save($writer)
        }
        finally {
            $writer.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }
}
finally {
    $zip.Dispose()
}

Write-Output "Yazildi: $output"
