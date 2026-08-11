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

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cimnastik.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
with app.app_context():
    db.drop_all() # Eski eksik tabloları tamamen siler
    db.create_all() # Yeni SiteIcerik dahil tüm tabloları sıfırdan kurar


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

# ANA SAYFA ROTASI (Tüm içerikleri ve branşları ön yüze gönderir)
@app.route('/')
def ana_sayfa():
    branslar = Brans.query.filter_by(aktif_mi=True).all()
    tum_icerikler = SiteIcerik.query.filter_by(aktif_mi=True).all()
    return render_template('index.html', branslar=branslar, icerikler=tum_icerikler)
# --- VİTRİN (ÖN YÜZ) YÖNLENDİRMELERİ ---
# --- VİTRİN (ÖN YÜZ) YÖNLENDİRMELERİ ---

@app.route('/icerik_ekle', methods=['POST'])
def icerik_ekle():
    try:
        tip = request.form.get('tip')
        baslik = request.form.get('baslik')
        aciklama = request.form.get('aciklama')
        resim_dosyasi = request.files.get('resim')

        resim_linki = ""
        if resim_dosyasi:
            yukleme_sonucu = cloudinary.uploader.upload(resim_dosyasi)
            resim_linki = yukleme_sonucu.get('secure_url')

        yeni_icerik = SiteIcerik(
            tip=tip,
            baslik=baslik,
            aciklama=aciklama,
            resim_url=resim_linki,
            aktif_mi=True
        )
        db.session.add(yeni_icerik)
        db.session.commit()

        return jsonify({"durum": True, "mesaj": "İçerik başarıyla eklendi ve sitede yayınlandı!"})
    except Exception as e:
        return jsonify({"durum": False, "mesaj": f"Hata: {str(e)}"})

# --- ARKADAŞININ GİRECEĞİ YÖNETİM PANELİ ---
@app.route('/site_yonetimi')
def site_yonetimi():
    return render_template('site_yonetimi.html')

# --- MEVCUT YÖNETİM (ARKA PLAN) YÖNLENDİRMELERİ ---
@app.route('/login', methods=['POST'])
def login():
    veri = request.json
    if veri['kadi'] == 'tolgahan' and veri['sifre'] == 'kaya3827':
        return jsonify({"mesaj": "Geliştirici Girişi Başarılı", "durum": True})

    kullanici = Kullanici.query.filter_by(kullanici_adi=veri['kadi'], sifre=veri['sifre']).first()
    if kullanici:
        return jsonify({"mesaj": "Giriş Başarılı", "durum": True})
        
    return jsonify({"mesaj": "Hatalı Kullanıcı Adı veya Şifre", "durum": False})

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
    
