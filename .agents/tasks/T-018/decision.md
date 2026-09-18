# T-018 karar — otomatik OCR dili seçimi

**KABUL — 18 Eylül 2026.** Otomatik dil seçimi Korece, Japonca, Çince ve İngilizce için
Snapshot akışına bağlıdır. Şerit aşaması dili düşük maliyetle seçer; dil değiştiğinde kazanan
motor doğru ekran koordinatlarını korumak için tam kareyi bir kez okur. Bu ek okuma sözleşmenin
parçasıdır; eski çağrı sayısı beklentileri güncellendi.

Doğrulama:

- Dil algılama ve Snapshot hedef testleri: 44 geçti.
- Gerçek model kontrolü: `.agents/tasks/T-018/real_check_sonuc.txt` temiz (6/6 dil sırası,
  Japonca uçtan uca çeviri, sonraki Snapshot tek OCR).
- T-019 ile birlikte tam takım: 2432 geçti.

Sınır: İlk yanlış dil durumunda aday motorlar ve kazanan tam kare okuması ek gecikme yaratır;
kazanan dil oturum boyunca korunarak sonraki okumalarda bu maliyet kaldırılır.

