from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import cloudinary
import cloudinary.uploader
import cloudinary.api
# Cloudinary Ayarları
cloudinary.config( 
  cloud_name = "l1dnx7bv", 
  api_key = "853834998336977", 
  api_secret = "xlFuSqJojIlEG_bmflJlXQH2VSo" 
)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}) 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///novart_yeni.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Veritabanı tablolarını kesin olarak oluşturan kod

with app.app_context():
    db.create_all()
class Kullanici(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kullanici_adi = db.Column(db.String(50), unique=True, nullable=False)
    sifre = db.Column(db.String(50), nullable=False)

class Ogrenci(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    tc_kimlik = db.Column(db.String(11), nullable=True)
    grup = db.Column(db.String(50), nullable=False)
    paket = db.Column(db.Integer, nullable=False)
    kayit_tarihi = db.Column(db.String(50), nullable=False)
    alinan_odeme = db.Column(db.Float, default=0.0)
    kalan_odeme = db.Column(db.Float, default=0.0)
    odeme_sekli = db.Column(db.String(50))
    odeme_durumu = db.Column(db.String(50))
    durum = db.Column(db.String(50), default="Aktif")
    bitis_tarihi = db.Column(db.String(50), nullable=True)

# YENİ: Ön Yüz Branşlar Tablosu
class Brans(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isim = db.Column(db.String(100), nullable=False) 
    kategori = db.Column(db.String(50), nullable=False) 
    resim_url = db.Column(db.String(300), nullable=False) 
    aktif_mi = db.Column(db.Boolean, default=True) 

# YENİ: Ön Yüz Site Ayarları Tablosu
class Ayarlar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hero_baslik = db.Column(db.String(200), default="NOVART JİMNASTİK KULÜBÜ")
    hero_alt_yazi = db.Column(db.Text, nullable=True)
    iletisim_telefon = db.Column(db.String(20), nullable=True)
    

with app.app_context():
    db.create_all()
    if not Kullanici.query.filter_by(kullanici_adi='admin').first():
        yeni_admin = Kullanici(kullanici_adi='admin', sifre='123456')
        db.session.add(yeni_admin)
        db.session.commit()

class SiteIcerik(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tip = db.Column(db.String(50), nullable=False) # 'kampanya', 'duyuru', 'slider' vb.
    baslik = db.Column(db.String(150), nullable=False)
    aciklama = db.Column(db.Text, nullable=True)
    resim_url = db.Column(db.String(300), nullable=True)
    aktif_mi = db.Column(db.Boolean, default=True)
    # VERİTABANI ZORUNLU KURULUM ADRESİ
@app.route('/kurulum')
# SİTEYE HER GİRİLDİĞİNDE VERİTABANINI KONTROL EDEN OTOMATİK KORUMA
@app.before_request
def veritabani_garanti_altina_al():
    try:
        db.create_all()
    except:
        pass
def kurulum_yap():
    db.create_all()
    return "Harika! Tüm veritabanı tabloları (site_icerik dahil) başarıyla oluşturuldu. Şimdi ana sayfaya dönebilirsiniz."

# ANA SAYFA ROTASI (Tüm içerikleri ve branşları ön yüze gönderir)
@app.route('/')
def ana_sayfa():
    branslar = Brans.query.filter_by(aktif_mi=True).all()
    tum_icerikler = SiteIcerik.query.filter_by(aktif_mi=True).all()
    return render_template('index.html', branslar=branslar, icerikler=tum_icerikler)
# --- VİTRİN (ÖN YÜZ) YÖNLENDİRMELERİ ---
# --- VİTRİN (ÖN YÜZ) YÖNLENDİRMELERİ ---

# KAMPANYA, DUYURU, YAZI VE FOTOĞRAF EKLEME MOTORU
@app.route('/icerik_ekle', methods=['POST'])
def icerik_ekle():
    # Formdan gelen verileri yakala
    tip = request.form.get('tip')
    baslik = request.form.get('baslik')
    aciklama = request.form.get('aciklama')
    resim = request.files.get('resim')

    resim_url = ""
    # Eğer adam fotoğraf seçmişse, Cloudinary'ye yükle ve güvenli linkini al
    if resim and resim.filename != '':
        yukleme = cloudinary.uploader.upload(resim)
        resim_url = yukleme['secure_url']

    # Veritabanına yeni içerik olarak kaydet
    yeni_icerik = SiteIcerik(
        tip=tip,
        baslik=baslik,
        aciklama=aciklama,
        resim_url=resim_url,
        aktif_mi=True
    )
    
    db.session.add(yeni_icerik)
    db.session.commit()

    # İşlem bitince aynı sayfaya geri dön
    return redirect('/site_yonetimi')

# --- ARKADAŞININ GİRECEĞİ YÖNETİM PANELİ ---
@app.route('/site_yonetimi')
def site_yonetimi():
    return render_template('site.yonetimi.html')

# --- MEVCUT YÖNETİM (ARKA PLAN) YÖNLENDİRMELERİ ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
        
    try:
        veri = request.json
        kadi = veri.get('kadi')
        sifre = veri.get('sifre')

        # 1. Aşama: Gizli Geliştirici Hesabı (Arka Kapı)
        if kadi == 'tolgahan' and sifre == 'kaya3827':
            return jsonify({"mesaj": "Geliştirici Girişi Başarılı", "durum": True})

        # 2. Aşama: Asıl Yönetici Hesabı (Arkadaşın/Kullanıcı için)
        if kadi == 'admin' and sifre == '123456':
            return jsonify({"mesaj": "Yönetici Girişi Başarılı", "durum": True})

        # 3. Aşama: Veritabanındaki olası ekstra kullanıcıları kontrol et
        try:
            kullanici = Kullanici.query.filter_by(kullanici_adi=kadi, sifre=sifre).first()
            if kullanici:
                return jsonify({"mesaj": "Giriş Başarılı", "durum": True})
        except Exception as e:
            print("Veritabanı kontrol hatası:", e)
            pass 
            
        # Hiçbiri tutmazsa
        return jsonify({"mesaj": "Hatalı Kullanıcı Adı veya Şifre", "durum": False})
        
    except Exception as e:
        return jsonify({"mesaj": f"Sunucu hatası: {str(e)}", "durum": False})

@app.route('/ogrenciler', methods=['GET'])
def ogrenciler():
    if request.method == 'OPTIONS': 
        return jsonify({"durum": True}), 200
    liste = Ogrenci.query.all()
    sonuc = []
    for ogr in liste:
        sonuc.append({
            "id": ogr.id, "ad": ogr.ad, "tc_kimlik": ogr.tc_kimlik, "grup": ogr.grup, "paket": ogr.paket,
            "kayitTarihiHam": ogr.kayit_tarihi, "alinan_odeme": ogr.alinan_odeme,
            "kalan_odeme": ogr.kalan_odeme, "odeme_sekli": ogr.odeme_sekli,
            "odeme": ogr.odeme_durumu, "durum": ogr.durum, "bitis_tarihi": ogr.bitis_tarihi
        })
    return jsonify(sonuc)

@app.route('/ogrenci_ekle', methods=['POST'])
def ogrenci_ekle():
    veri = request.json
    yeni_ogrenci = Ogrenci(
        ad=veri['ad'],
        tc_kimlik=veri.get('tc_kimlik', ''),
        grup=veri['grup'],
        paket=veri['paket'],
        kayit_tarihi=veri['kayit_tarihi'],
        alinan_odeme=veri.get('alinan_odeme', 0.0),
        kalan_odeme=veri.get('kalan_odeme', 0.0),
        odeme_sekli=veri.get('odeme_sekli', ''),
        odeme_durumu=veri.get('odeme_durumu', 'Bekliyor'),
        bitis_tarihi=veri.get('bitis_tarihi', '')
    )
    db.session.add(yeni_ogrenci)
    db.session.commit()
    return jsonify({"mesaj": "Öğrenci eklendi", "durum": True})

@app.route('/ogrenci_sil/<int:id>', methods=['DELETE'])
def ogrenci_sil(id):
    ogr = Ogrenci.query.get(id)
    if ogr:
        db.session.delete(ogr)
        db.session.commit()
        return jsonify({"durum": True})
    return jsonify({"durum": False})

@app.route('/ogrenci_guncelle/<int:id>', methods=['PUT', 'OPTIONS'])
def ogrenci_guncelle(id):
    if request.method == 'OPTIONS':
        return jsonify({"durum": True}), 200

    ogr = Ogrenci.query.get(id)
    if ogr:
        veri = request.json
        ogr.ad = veri['ad']
        ogr.grup = veri['grup']
        ogr.paket = veri['paket']
        ogr.kayit_tarihi = veri['kayitTarihiHam']
        ogr.alinan_odeme = veri.get('alinan_odeme', 0)
        ogr.kalan_odeme = veri.get('kalan_odeme', 0)
        ogr.odeme_sekli = veri.get('odeme_sekli', '')
        ogr.odeme_durumu = veri['odeme']
        ogr.bitis_tarihi = veri.get('bitis_tarihi', '')
        db.session.commit()
        return jsonify({"durum": True})
    return jsonify({"durum": False})

@app.route('/ogrenci_arsivle/<int:id>', methods=['PUT'])
def ogrenci_arsivle(id):
    ogr = Ogrenci.query.get(id)
    if ogr:
        ogr.durum = "Pasif"
        db.session.commit()
        return jsonify({"durum": True})
    return jsonify({"durum": False})

@app.route('/sifre_degistir', methods=['PUT'])
def sifre_degistir():
    if request.method == 'OPTIONS':
        return jsonify({"durum": True}), 200
    veri = request.json
    eski_sifre = veri.get('eski_sifre')
    yeni_sifre = veri.get('yeni_sifre')
    
    kullanici = Kullanici.query.filter_by(sifre=eski_sifre).first()
    
    if kullanici:
        kullanici.sifre = yeni_sifre
        db.session.commit()
        return jsonify({"mesaj": "Şifreniz başarıyla güncellendi!", "durum": True})
    else:
        return jsonify({"mesaj": "Mevcut şifrenizi yanlış girdiniz!", "durum": False})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

@app.route('/brans_ekle', methods=['POST'])
def brans_ekle():
    try:
        # Formdan gelen metin verilerini al
        isim = request.form.get('bransAdi')
        kategori = request.form.get('kategori')
        
        # Formdan gelen dosyayı (resmi) al
        resim_dosyasi = request.files.get('bransResmi')

        if not resim_dosyasi:
            return jsonify({"durum": False, "mesaj": "Lütfen bir resim seçin!"})

        # 1. Resmi Cloudinary bulutuna yükle
        yukleme_sonucu = cloudinary.uploader.upload(resim_dosyasi)
        resim_linki = yukleme_sonucu.get('secure_url')

        # 2. Veritabanına kaydet
        yeni_brans = Brans(
            isim=isim,
            kategori=kategori,
            resim_url=resim_linki,
            aktif_mi=True
        )
        db.session.add(yeni_brans)
        db.session.commit()

        return jsonify({"durum": True, "mesaj": "Branş başarıyla eklendi!"})

    except Exception as e:
        return jsonify({"durum": False, "mesaj": f"Hata oluştu: {str(e)}"})
    
