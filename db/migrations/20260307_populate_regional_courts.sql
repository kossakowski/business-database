/*
 * Migration: Populate Regional Courts
 * Date: 2026-03-07
 * Description: Inserts all 319 regional courts into regional_court_lookup
 *              and courts.courts tables with correct parent hierarchies.
 *
 * Sources:
 * - SAOS API (hierarchy): https://www.saos.org.pl/api/dump/commonCourts
 * - dane.gov.pl (authoritative names): dataset 985, resource 65134
 * - Manual research for courts not in SAOS (Czeladź, Warszawa m.st.)
 * - District reassignments: Rybnik (est. 2020), Sosnowiec (est. 2022)
 */

BEGIN;

-- 1. Clean existing sample regional courts
DELETE FROM courts.courts WHERE kind = 'regional';
DELETE FROM courts.regional_court_lookup WHERE code LIKE 'sad_rejonowy_%';

-- 2. Populate regional_court_lookup (319 entries)
INSERT INTO courts.regional_court_lookup (code, name, district_code, city) VALUES
    ('sad_rejonowy_bialymstoku', 'Sąd Rejonowy w Białymstoku', 'sad_okregowy_bialystok', 'Białystok'),
    ('sad_rejonowy_bielsku_podlaskim', 'Sąd Rejonowy w Bielsku Podlaskim', 'sad_okregowy_bialystok', 'Bielsk Podlaski'),
    ('sad_rejonowy_sokolce', 'Sąd Rejonowy w Sokółce', 'sad_okregowy_bialystok', 'Sokółka'),
    ('sad_rejonowy_bielsku_bialej', 'Sąd Rejonowy w Bielsku-Białej', 'sad_okregowy_bielsko_biala', 'Bielsko-Biała'),
    ('sad_rejonowy_cieszynie', 'Sąd Rejonowy w Cieszynie', 'sad_okregowy_bielsko_biala', 'Cieszyn'),
    ('sad_rejonowy_zywcu', 'Sąd Rejonowy w Żywcu', 'sad_okregowy_bielsko_biala', 'Żywiec'),
    ('sad_rejonowy_bydgoszczy', 'Sąd Rejonowy w Bydgoszczy', 'sad_okregowy_bydgoszcz', 'Bydgoszcz'),
    ('sad_rejonowy_inowroclawiu', 'Sąd Rejonowy w Inowrocławiu', 'sad_okregowy_bydgoszcz', 'Inowrocław'),
    ('sad_rejonowy_mogilnie', 'Sąd Rejonowy w Mogilnie', 'sad_okregowy_bydgoszcz', 'Mogilno'),
    ('sad_rejonowy_nakle_nad_notecia', 'Sąd Rejonowy w Nakle nad Notecią', 'sad_okregowy_bydgoszcz', 'Nakło nad Notecią'),
    ('sad_rejonowy_swieciu', 'Sąd Rejonowy w Świeciu', 'sad_okregowy_bydgoszcz', 'Świecie'),
    ('sad_rejonowy_szubinie', 'Sąd Rejonowy w Szubinie', 'sad_okregowy_bydgoszcz', 'Szubin'),
    ('sad_rejonowy_tucholi', 'Sąd Rejonowy w Tucholi', 'sad_okregowy_bydgoszcz', 'Tuchola'),
    ('sad_rejonowy_zninie', 'Sąd Rejonowy w Żninie', 'sad_okregowy_bydgoszcz', 'Żnin'),
    ('sad_rejonowy_czestochowie', 'Sąd Rejonowy w Częstochowie', 'sad_okregowy_czestochowa', 'Częstochowa'),
    ('sad_rejonowy_lublincu', 'Sąd Rejonowy w Lublińcu', 'sad_okregowy_czestochowa', 'Lubliniec'),
    ('sad_rejonowy_myszkowie', 'Sąd Rejonowy w Myszkowie', 'sad_okregowy_czestochowa', 'Myszków'),
    ('sad_rejonowy_braniewie', 'Sąd Rejonowy w Braniewie', 'sad_okregowy_elblag', 'Braniewo'),
    ('sad_rejonowy_dzialdowie', 'Sąd Rejonowy w Działdowie', 'sad_okregowy_elblag', 'Działdów'),
    ('sad_rejonowy_elblagu', 'Sąd Rejonowy w Elblągu', 'sad_okregowy_elblag', 'Elbląg'),
    ('sad_rejonowy_ilawie', 'Sąd Rejonowy w Iławie', 'sad_okregowy_elblag', 'Iława'),
    ('sad_rejonowy_nowym_miescie_lubawskim', 'Sąd Rejonowy w Nowym Mieście Lubawskim', 'sad_okregowy_elblag', 'Nowe Miasto Lubawskie'),
    ('sad_rejonowy_ostrodzie', 'Sąd Rejonowy w Ostródzie', 'sad_okregowy_elblag', 'Ostród'),
    ('sad_rejonowy_gdansk_polnoc', 'Sąd Rejonowy Gdańsk-Północ w Gdańsku', 'sad_okregowy_gdansk', 'Gdańsk'),
    ('sad_rejonowy_gdansk_poludnie', 'Sąd Rejonowy Gdańsk-Południe w Gdańsku', 'sad_okregowy_gdansk', 'Gdańsk'),
    ('sad_rejonowy_gdyni', 'Sąd Rejonowy w Gdyni', 'sad_okregowy_gdansk', 'Gdynia'),
    ('sad_rejonowy_kartuzach', 'Sąd Rejonowy w Kartuzach', 'sad_okregowy_gdansk', 'Kartuzy'),
    ('sad_rejonowy_koscierzynie', 'Sąd Rejonowy w Kościerzynie', 'sad_okregowy_gdansk', 'Kościerzyna'),
    ('sad_rejonowy_kwidzynie', 'Sąd Rejonowy w Kwidzynie', 'sad_okregowy_gdansk', 'Kwidzyn'),
    ('sad_rejonowy_malborku', 'Sąd Rejonowy w Malborku', 'sad_okregowy_gdansk', 'Malbork'),
    ('sad_rejonowy_sopocie', 'Sąd Rejonowy w Sopocie', 'sad_okregowy_gdansk', 'Sopot'),
    ('sad_rejonowy_starogardzie_gdanskim', 'Sąd Rejonowy w Starogardzie Gdańskim', 'sad_okregowy_gdansk', 'Starogard Gdański'),
    ('sad_rejonowy_tczewie', 'Sąd Rejonowy w Tczewie', 'sad_okregowy_gdansk', 'Tczew'),
    ('sad_rejonowy_wejherowie', 'Sąd Rejonowy w Wejherowie', 'sad_okregowy_gdansk', 'Wejherów'),
    ('sad_rejonowy_gliwicach', 'Sąd Rejonowy w Gliwicach', 'sad_okregowy_gliwice', 'Gliwice'),
    ('sad_rejonowy_rudzie_slaskiej', 'Sąd Rejonowy w Rudzie Śląskiej', 'sad_okregowy_gliwice', 'Ruda Śląska'),
    ('sad_rejonowy_tarnowskich_gorach', 'Sąd Rejonowy w Tarnowskich Górach', 'sad_okregowy_gliwice', 'Tarnowskie Góry'),
    ('sad_rejonowy_zabrzu', 'Sąd Rejonowy w Zabrzu', 'sad_okregowy_gliwice', 'Zabrze'),
    ('sad_rejonowy_gorzowie_wielkopolskim', 'Sąd Rejonowy w Gorzowie Wielkopolskim', 'sad_okregowy_gorzow_wielkopolski', 'Gorzów Wielkopolski'),
    ('sad_rejonowy_miedzyrzeczu', 'Sąd Rejonowy w Międzyrzeczu', 'sad_okregowy_gorzow_wielkopolski', 'Międzyrzecz'),
    ('sad_rejonowy_slubicach', 'Sąd Rejonowy w Słubicach', 'sad_okregowy_gorzow_wielkopolski', 'Słubice'),
    ('sad_rejonowy_strzelcach_krajenskich', 'Sąd Rejonowy w Strzelcach Krajeńskich', 'sad_okregowy_gorzow_wielkopolski', 'Strzelce Krajeńskie'),
    ('sad_rejonowy_sulecinie', 'Sąd Rejonowy w Sulęcinie', 'sad_okregowy_gorzow_wielkopolski', 'Sulęcin'),
    ('sad_rejonowy_boleslawcu', 'Sąd Rejonowy w Bolesławcu', 'sad_okregowy_jelenia_gora', 'Bolesławiec'),
    ('sad_rejonowy_jeleniej_gorze', 'Sąd Rejonowy w Jeleniej Górze', 'sad_okregowy_jelenia_gora', 'Jelenia Góra'),
    ('sad_rejonowy_kamiennej_gorze', 'Sąd Rejonowy w Kamiennej Górze', 'sad_okregowy_jelenia_gora', 'Kamienna Góra'),
    ('sad_rejonowy_lubaniu', 'Sąd Rejonowy w Lubaniu', 'sad_okregowy_jelenia_gora', 'Lubań'),
    ('sad_rejonowy_lwowku_slaskim', 'Sąd Rejonowy w Lwówku Śląskim', 'sad_okregowy_jelenia_gora', 'Lwówek Śląski'),
    ('sad_rejonowy_zgorzelcu', 'Sąd Rejonowy w Zgorzelcu', 'sad_okregowy_jelenia_gora', 'Zgorzelec'),
    ('sad_rejonowy_jarocinie', 'Sąd Rejonowy w Jarocinie', 'sad_okregowy_kalisz', 'Jarocin'),
    ('sad_rejonowy_kaliszu', 'Sąd Rejonowy w Kaliszu', 'sad_okregowy_kalisz', 'Kalisz'),
    ('sad_rejonowy_kepnie', 'Sąd Rejonowy w Kępnie', 'sad_okregowy_kalisz', 'Kępno'),
    ('sad_rejonowy_krotoszynie', 'Sąd Rejonowy w Krotoszynie', 'sad_okregowy_kalisz', 'Krotoszyn'),
    ('sad_rejonowy_ostrowie_wielkopolskim', 'Sąd Rejonowy w Ostrowie Wielkopolskim', 'sad_okregowy_kalisz', 'Ostrów Wielkopolski'),
    ('sad_rejonowy_ostrzeszowie', 'Sąd Rejonowy w Ostrzeszowie', 'sad_okregowy_kalisz', 'Ostrzeszów'),
    ('sad_rejonowy_pleszewie', 'Sąd Rejonowy w Pleszewie', 'sad_okregowy_kalisz', 'Pleszew'),
    ('sad_rejonowy_bytomiu', 'Sąd Rejonowy w Bytomiu', 'sad_okregowy_katowice', 'Bytom'),
    ('sad_rejonowy_chorzowie', 'Sąd Rejonowy w Chorzowie', 'sad_okregowy_katowice', 'Chorzów'),
    ('sad_rejonowy_katowice_wschod', 'Sąd Rejonowy Katowice-Wschód w Katowicach', 'sad_okregowy_katowice', 'Katowice'),
    ('sad_rejonowy_katowice_zachod', 'Sąd Rejonowy Katowice-Zachód w Katowicach', 'sad_okregowy_katowice', 'Katowice'),
    ('sad_rejonowy_mikolowie', 'Sąd Rejonowy w Mikołowie', 'sad_okregowy_katowice', 'Mikołów'),
    ('sad_rejonowy_myslowicach', 'Sąd Rejonowy w Mysłowicach', 'sad_okregowy_katowice', 'Mysłowice'),
    ('sad_rejonowy_pszczynie', 'Sąd Rejonowy w Pszczynie', 'sad_okregowy_katowice', 'Pszczyna'),
    ('sad_rejonowy_siemianowicach_slaskich', 'Sąd Rejonowy w Siemianowicach Śląskich', 'sad_okregowy_katowice', 'Siemianowice Śląskie'),
    ('sad_rejonowy_tychach', 'Sąd Rejonowy w Tychach', 'sad_okregowy_katowice', 'Tychy'),
    ('sad_rejonowy_busku_zdroju', 'Sąd Rejonowy w Busku-Zdroju', 'sad_okregowy_kielce', 'Busko-Zdrój'),
    ('sad_rejonowy_jedrzejowie', 'Sąd Rejonowy w Jędrzejowie', 'sad_okregowy_kielce', 'Jędrzejów'),
    ('sad_rejonowy_kielcach', 'Sąd Rejonowy w Kielcach', 'sad_okregowy_kielce', 'Kielce'),
    ('sad_rejonowy_konskich', 'Sąd Rejonowy w Końskich', 'sad_okregowy_kielce', 'Końskie'),
    ('sad_rejonowy_opatowie', 'Sąd Rejonowy w Opatowie', 'sad_okregowy_kielce', 'Opatów'),
    ('sad_rejonowy_ostrowcu_swietokrzyskim', 'Sąd Rejonowy w Ostrowcu Świętokrzyskim', 'sad_okregowy_kielce', 'Ostrowiec Świętokrzyski'),
    ('sad_rejonowy_pinczowie', 'Sąd Rejonowy w Pińczowie', 'sad_okregowy_kielce', 'Pińczów'),
    ('sad_rejonowy_sandomierzu', 'Sąd Rejonowy w Sandomierzu', 'sad_okregowy_kielce', 'Sandomierz'),
    ('sad_rejonowy_skarzysku_kamiennej', 'Sąd Rejonowy w Skarżysku-Kamiennej', 'sad_okregowy_kielce', 'Skarżysko-Kamienna'),
    ('sad_rejonowy_starachowicach', 'Sąd Rejonowy w Starachowicach', 'sad_okregowy_kielce', 'Starachowice'),
    ('sad_rejonowy_staszowie', 'Sąd Rejonowy w Staszowie', 'sad_okregowy_kielce', 'Staszów'),
    ('sad_rejonowy_wloszczowie', 'Sąd Rejonowy we Włoszczowie', 'sad_okregowy_kielce', 'Włoszczów'),
    ('sad_rejonowy_kole', 'Sąd Rejonowy w Kole', 'sad_okregowy_konin', 'Koło'),
    ('sad_rejonowy_koninie', 'Sąd Rejonowy w Koninie', 'sad_okregowy_konin', 'Konin'),
    ('sad_rejonowy_slupcy', 'Sąd Rejonowy w Słupcy', 'sad_okregowy_konin', 'Słupca'),
    ('sad_rejonowy_turku', 'Sąd Rejonowy w Turku', 'sad_okregowy_konin', 'Turek'),
    ('sad_rejonowy_bialogardzie', 'Sąd Rejonowy w Białogardzie', 'sad_okregowy_koszalin', 'Białogard'),
    ('sad_rejonowy_drawsku_pomorskim', 'Sąd Rejonowy w Drawsku Pomorskim', 'sad_okregowy_koszalin', 'Drawsko Pomorskie'),
    ('sad_rejonowy_kolobrzegu', 'Sąd Rejonowy w Kołobrzegu', 'sad_okregowy_koszalin', 'Kołobrzeg'),
    ('sad_rejonowy_koszalinie', 'Sąd Rejonowy w Koszalinie', 'sad_okregowy_koszalin', 'Koszalin'),
    ('sad_rejonowy_slawnie', 'Sąd Rejonowy w Sławnie', 'sad_okregowy_koszalin', 'Sławno'),
    ('sad_rejonowy_szczecinku', 'Sąd Rejonowy w Szczecinku', 'sad_okregowy_koszalin', 'Szczecinek'),
    ('sad_rejonowy_walczu', 'Sąd Rejonowy w Wałczu', 'sad_okregowy_koszalin', 'Wałcz'),
    ('sad_rejonowy_chrzanowie', 'Sąd Rejonowy w Chrzanowie', 'sad_okregowy_krakow', 'Chrzanów'),
    ('sad_rejonowy_krakowa_krowodrzy', 'Sąd Rejonowy dla Krakowa-Krowodrzy w Krakowie', 'sad_okregowy_krakow', 'Kraków'),
    ('sad_rejonowy_krakowa_nowej_huty', 'Sąd Rejonowy dla Krakowa-Nowej Huty w Krakowie', 'sad_okregowy_krakow', 'Kraków'),
    ('sad_rejonowy_krakowa_podgorza', 'Sąd Rejonowy dla Krakowa-Podgórza w Krakowie', 'sad_okregowy_krakow', 'Kraków'),
    ('sad_rejonowy_krakowa_srodmiescia', 'Sąd Rejonowy dla Krakowa-Śródmieścia w Krakowie', 'sad_okregowy_krakow', 'Kraków'),
    ('sad_rejonowy_miechowie', 'Sąd Rejonowy w Miechowie', 'sad_okregowy_krakow', 'Miechów'),
    ('sad_rejonowy_myslenicach', 'Sąd Rejonowy w Myślenicach', 'sad_okregowy_krakow', 'Myślenice'),
    ('sad_rejonowy_olkuszu', 'Sąd Rejonowy w Olkuszu', 'sad_okregowy_krakow', 'Olkusz'),
    ('sad_rejonowy_oswiecimiu', 'Sąd Rejonowy w Oświęcimiu', 'sad_okregowy_krakow', 'Oświęcim'),
    ('sad_rejonowy_suchej_beskidzkiej', 'Sąd Rejonowy w Suchej Beskidzkiej', 'sad_okregowy_krakow', 'Sucha Beskidzka'),
    ('sad_rejonowy_wadowicach', 'Sąd Rejonowy w Wadowicach', 'sad_okregowy_krakow', 'Wadowice'),
    ('sad_rejonowy_wieliczce', 'Sąd Rejonowy w Wieliczce', 'sad_okregowy_krakow', 'Wieliczka'),
    ('sad_rejonowy_brzozowie', 'Sąd Rejonowy w Brzozowie', 'sad_okregowy_krosno', 'Brzozów'),
    ('sad_rejonowy_jasle', 'Sąd Rejonowy w Jaśle', 'sad_okregowy_krosno', 'Jasło'),
    ('sad_rejonowy_krosnie', 'Sąd Rejonowy w Krośnie', 'sad_okregowy_krosno', 'Krosno'),
    ('sad_rejonowy_lesku', 'Sąd Rejonowy w Lesku', 'sad_okregowy_krosno', 'Lesk'),
    ('sad_rejonowy_sanoku', 'Sąd Rejonowy w Sanoku', 'sad_okregowy_krosno', 'Sanok'),
    ('sad_rejonowy_glogowie', 'Sąd Rejonowy w Głogowie', 'sad_okregowy_legnica', 'Głogów'),
    ('sad_rejonowy_jaworze', 'Sąd Rejonowy w Jaworze', 'sad_okregowy_legnica', 'Jawor'),
    ('sad_rejonowy_legnicy', 'Sąd Rejonowy w Legnicy', 'sad_okregowy_legnica', 'Legnica'),
    ('sad_rejonowy_lubinie', 'Sąd Rejonowy w Lubinie', 'sad_okregowy_legnica', 'Lubin'),
    ('sad_rejonowy_zlotoryi', 'Sąd Rejonowy w Złotoryi', 'sad_okregowy_legnica', 'Złotoryja'),
    ('sad_rejonowy_brzezinach', 'Sąd Rejonowy w Brzezinach', 'sad_okregowy_lodz', 'Brzeziny'),
    ('sad_rejonowy_kutnie', 'Sąd Rejonowy w Kutnie', 'sad_okregowy_lodz', 'Kutno'),
    ('sad_rejonowy_leczycy', 'Sąd Rejonowy w Łęczycy', 'sad_okregowy_lodz', 'Łęczyca'),
    ('sad_rejonowy_lodzi_srodmiescia', 'Sąd Rejonowy dla Łodzi-Śródmieścia w Łodzi', 'sad_okregowy_lodz', 'Łódź'),
    ('sad_rejonowy_lodzi_widzewa', 'Sąd Rejonowy dla Łodzi-Widzewa w Łodzi', 'sad_okregowy_lodz', 'Łódź'),
    ('sad_rejonowy_lowiczu', 'Sąd Rejonowy w Łowiczu', 'sad_okregowy_lodz', 'Łowicz'),
    ('sad_rejonowy_pabianicach', 'Sąd Rejonowy w Pabianicach', 'sad_okregowy_lodz', 'Pabianice'),
    ('sad_rejonowy_rawie_mazowieckiej', 'Sąd Rejonowy w Rawie Mazowieckiej', 'sad_okregowy_lodz', 'Rawa Mazowiecka'),
    ('sad_rejonowy_skierniewicach', 'Sąd Rejonowy w Skierniewicach', 'sad_okregowy_lodz', 'Skierniewice'),
    ('sad_rejonowy_zgierzu', 'Sąd Rejonowy w Zgierzu', 'sad_okregowy_lodz', 'Zgierz'),
    ('sad_rejonowy_grajewie', 'Sąd Rejonowy w Grajewie', 'sad_okregowy_lomza', 'Grajewo'),
    ('sad_rejonowy_lomzy', 'Sąd Rejonowy w Łomży', 'sad_okregowy_lomza', 'Łomża'),
    ('sad_rejonowy_wysokiem_mazowieckiem', 'Sąd Rejonowy w Wysokiem Mazowieckiem', 'sad_okregowy_lomza', 'Wysokie Mazowieckie'),
    ('sad_rejonowy_zambrowie', 'Sąd Rejonowy w Zambrowie', 'sad_okregowy_lomza', 'Zambrów'),
    ('sad_rejonowy_bialej_podlaskiej', 'Sąd Rejonowy w Białej Podlaskiej', 'sad_okregowy_lublin', 'Biała Podlaska'),
    ('sad_rejonowy_chelmie', 'Sąd Rejonowy w Chełmie', 'sad_okregowy_lublin', 'Chełm'),
    ('sad_rejonowy_krasniku', 'Sąd Rejonowy w Kraśniku', 'sad_okregowy_lublin', 'Kraśnik'),
    ('sad_rejonowy_lubartowie', 'Sąd Rejonowy w Lubartowie', 'sad_okregowy_lublin', 'Lubartów'),
    ('sad_rejonowy_lublin_wschod', 'Sąd Rejonowy Lublin-Wschód w Lublinie z siedzibą w Świdniku', 'sad_okregowy_lublin', 'Świdnik'),
    ('sad_rejonowy_lublin_zachod', 'Sąd Rejonowy Lublin-Zachód w Lublinie', 'sad_okregowy_lublin', 'Lublin'),
    ('sad_rejonowy_lukowie', 'Sąd Rejonowy w Łukowie', 'sad_okregowy_lublin', 'Łuków'),
    ('sad_rejonowy_opolu_lubelskim', 'Sąd Rejonowy w Opolu Lubelskim', 'sad_okregowy_lublin', 'Opole Lubelskie'),
    ('sad_rejonowy_pulawach', 'Sąd Rejonowy w Puławach', 'sad_okregowy_lublin', 'Puławy'),
    ('sad_rejonowy_radzyniu_podlaskim', 'Sąd Rejonowy w Radzyniu Podlaskim', 'sad_okregowy_lublin', 'Radzyń Podlaski'),
    ('sad_rejonowy_rykach', 'Sąd Rejonowy w Rykach', 'sad_okregowy_lublin', 'Ryki'),
    ('sad_rejonowy_wlodawie', 'Sąd Rejonowy we Włodawie', 'sad_okregowy_lublin', 'Włodawa'),
    ('sad_rejonowy_gorlicach', 'Sąd Rejonowy w Gorlicach', 'sad_okregowy_nowy_sacz', 'Gorlice'),
    ('sad_rejonowy_limanowej', 'Sąd Rejonowy w Limanowej', 'sad_okregowy_nowy_sacz', 'Limanowa'),
    ('sad_rejonowy_nowym_saczu', 'Sąd Rejonowy w Nowym Sączu', 'sad_okregowy_nowy_sacz', 'Nowy Sącz'),
    ('sad_rejonowy_nowym_targu', 'Sąd Rejonowy w Nowym Targu', 'sad_okregowy_nowy_sacz', 'Nowy Targ'),
    ('sad_rejonowy_zakopanem', 'Sąd Rejonowy w Zakopanem', 'sad_okregowy_nowy_sacz', 'Zakopane'),
    ('sad_rejonowy_bartoszycach', 'Sąd Rejonowy w Bartoszycach', 'sad_okregowy_olsztyn', 'Bartoszyce'),
    ('sad_rejonowy_biskupcu', 'Sąd Rejonowy w Biskupcu', 'sad_okregowy_olsztyn', 'Biskupiec'),
    ('sad_rejonowy_gizycku', 'Sąd Rejonowy w Giżycku', 'sad_okregowy_olsztyn', 'Giżycko'),
    ('sad_rejonowy_ketrzynie', 'Sąd Rejonowy w Kętrzynie', 'sad_okregowy_olsztyn', 'Kętrzyn'),
    ('sad_rejonowy_lidzbarku_warminskim', 'Sąd Rejonowy w Lidzbarku Warmińskim', 'sad_okregowy_olsztyn', 'Lidzbark Warmiński'),
    ('sad_rejonowy_mragowie', 'Sąd Rejonowy w Mrągowie', 'sad_okregowy_olsztyn', 'Mrągów'),
    ('sad_rejonowy_nidzicy', 'Sąd Rejonowy w Nidzicy', 'sad_okregowy_olsztyn', 'Nidzica'),
    ('sad_rejonowy_olsztynie', 'Sąd Rejonowy w Olsztynie', 'sad_okregowy_olsztyn', 'Olsztyn'),
    ('sad_rejonowy_piszu', 'Sąd Rejonowy w Piszu', 'sad_okregowy_olsztyn', 'Pisz'),
    ('sad_rejonowy_szczytnie', 'Sąd Rejonowy w Szczytnie', 'sad_okregowy_olsztyn', 'Szczytno'),
    ('sad_rejonowy_brzegu', 'Sąd Rejonowy w Brzegu', 'sad_okregowy_opole', 'Brzeg'),
    ('sad_rejonowy_glubczycach', 'Sąd Rejonowy w Głubczycach', 'sad_okregowy_opole', 'Głubczyce'),
    ('sad_rejonowy_kedzierzynie_kozlu', 'Sąd Rejonowy w Kędzierzynie-Koźlu', 'sad_okregowy_opole', 'Kędzierzyn-Koźle'),
    ('sad_rejonowy_kluczborku', 'Sąd Rejonowy w Kluczborku', 'sad_okregowy_opole', 'Kluczbork'),
    ('sad_rejonowy_nysie', 'Sąd Rejonowy w Nysie', 'sad_okregowy_opole', 'Nysa'),
    ('sad_rejonowy_olesnie', 'Sąd Rejonowy w Oleśnie', 'sad_okregowy_opole', 'Oleśno'),
    ('sad_rejonowy_opolu', 'Sąd Rejonowy w Opolu', 'sad_okregowy_opole', 'Opole'),
    ('sad_rejonowy_prudniku', 'Sąd Rejonowy w Prudniku', 'sad_okregowy_opole', 'Prudnik'),
    ('sad_rejonowy_strzelcach_opolskich', 'Sąd Rejonowy w Strzelcach Opolskich', 'sad_okregowy_opole', 'Strzelce Opolskie'),
    ('sad_rejonowy_ostrolece', 'Sąd Rejonowy w Ostrołęce', 'sad_okregowy_ostroleka', 'Ostrołęka'),
    ('sad_rejonowy_ostrowi_mazowieckiej', 'Sąd Rejonowy w Ostrowi Mazowieckiej', 'sad_okregowy_ostroleka', 'Ostrów Mazowiecka'),
    ('sad_rejonowy_przasnyszu', 'Sąd Rejonowy w Przasnyszu', 'sad_okregowy_ostroleka', 'Przasnysz'),
    ('sad_rejonowy_pultusku', 'Sąd Rejonowy w Pułtusku', 'sad_okregowy_ostroleka', 'Pułtusk'),
    ('sad_rejonowy_wyszkowie', 'Sąd Rejonowy w Wyszkowie', 'sad_okregowy_ostroleka', 'Wyszków'),
    ('sad_rejonowy_belchatowie', 'Sąd Rejonowy w Bełchatowie', 'sad_okregowy_piotrkow_trybunalski', 'Bełchatów'),
    ('sad_rejonowy_opocznie', 'Sąd Rejonowy w Opocznie', 'sad_okregowy_piotrkow_trybunalski', 'Opoczno'),
    ('sad_rejonowy_piotrkowie_trybunalskim', 'Sąd Rejonowy w Piotrkowie Trybunalskim', 'sad_okregowy_piotrkow_trybunalski', 'Piotrków Trybunalski'),
    ('sad_rejonowy_radomsku', 'Sąd Rejonowy w Radomsku', 'sad_okregowy_piotrkow_trybunalski', 'Radomsk'),
    ('sad_rejonowy_tomaszowie_mazowieckim', 'Sąd Rejonowy w Tomaszowie Mazowieckim', 'sad_okregowy_piotrkow_trybunalski', 'Tomaszów Mazowiecki'),
    ('sad_rejonowy_ciechanowie', 'Sąd Rejonowy w Ciechanowie', 'sad_okregowy_plock', 'Ciechanów'),
    ('sad_rejonowy_gostyninie', 'Sąd Rejonowy w Gostyninie', 'sad_okregowy_plock', 'Gostynin'),
    ('sad_rejonowy_mlawie', 'Sąd Rejonowy w Mławie', 'sad_okregowy_plock', 'Mława'),
    ('sad_rejonowy_plocku', 'Sąd Rejonowy w Płocku', 'sad_okregowy_plock', 'Płock'),
    ('sad_rejonowy_plonsku', 'Sąd Rejonowy w Płońsku', 'sad_okregowy_plock', 'Płońsk'),
    ('sad_rejonowy_sierpcu', 'Sąd Rejonowy w Sierpcu', 'sad_okregowy_plock', 'Sierpc'),
    ('sad_rejonowy_sochaczewie', 'Sąd Rejonowy w Sochaczewie', 'sad_okregowy_plock', 'Sochaczew'),
    ('sad_rejonowy_zyrardowie', 'Sąd Rejonowy w Żyrardowie', 'sad_okregowy_plock', 'Żyrardów'),
    ('sad_rejonowy_chodziezy', 'Sąd Rejonowy w Chodzieży', 'sad_okregowy_poznan', 'Chodzież'),
    ('sad_rejonowy_gnieznie', 'Sąd Rejonowy w Gnieźnie', 'sad_okregowy_poznan', 'Gniezno'),
    ('sad_rejonowy_gostyniu', 'Sąd Rejonowy w Gostyniu', 'sad_okregowy_poznan', 'Gostyń'),
    ('sad_rejonowy_grodzisku_wielkopolskim', 'Sąd Rejonowy w Grodzisku Wielkopolskim', 'sad_okregowy_poznan', 'Grodzisk Wielkopolski'),
    ('sad_rejonowy_koscianie', 'Sąd Rejonowy w Kościanie', 'sad_okregowy_poznan', 'Kościan'),
    ('sad_rejonowy_lesznie', 'Sąd Rejonowy w Lesznie', 'sad_okregowy_poznan', 'Leszno'),
    ('sad_rejonowy_nowym_tomyslu', 'Sąd Rejonowy w Nowym Tomyślu', 'sad_okregowy_poznan', 'Nowy Tomyśl'),
    ('sad_rejonowy_obornikach', 'Sąd Rejonowy w Obornikach', 'sad_okregowy_poznan', 'Oborniki'),
    ('sad_rejonowy_pile', 'Sąd Rejonowy w Pile', 'sad_okregowy_poznan', 'Piła'),
    ('sad_rejonowy_poznan_grunwald_i_jezyce', 'Sąd Rejonowy Poznań-Grunwald i Jeżyce w Poznaniu', 'sad_okregowy_poznan', 'Poznań'),
    ('sad_rejonowy_poznan_nowe_miasto_i_wilda', 'Sąd Rejonowy Poznań-Nowe Miasto i Wilda w Poznaniu', 'sad_okregowy_poznan', 'Poznań'),
    ('sad_rejonowy_poznan_stare_miasto', 'Sąd Rejonowy Poznań-Stare Miasto w Poznaniu', 'sad_okregowy_poznan', 'Poznań'),
    ('sad_rejonowy_rawiczu', 'Sąd Rejonowy w Rawiczu', 'sad_okregowy_poznan', 'Rawicz'),
    ('sad_rejonowy_sremie', 'Sąd Rejonowy w Śremie', 'sad_okregowy_poznan', 'Śrem'),
    ('sad_rejonowy_srodzie_wielkopolskiej', 'Sąd Rejonowy w Środzie Wielkopolskiej', 'sad_okregowy_poznan', 'Środa Wielkopolska'),
    ('sad_rejonowy_szamotulach', 'Sąd Rejonowy w Szamotułach', 'sad_okregowy_poznan', 'Szamotuły'),
    ('sad_rejonowy_trzciance', 'Sąd Rejonowy w Trzciance', 'sad_okregowy_poznan', 'Trzcianka'),
    ('sad_rejonowy_wagrowcu', 'Sąd Rejonowy w Wągrowcu', 'sad_okregowy_poznan', 'Wągrowiec'),
    ('sad_rejonowy_wolsztynie', 'Sąd Rejonowy w Wolsztynie', 'sad_okregowy_poznan', 'Wolsztyn'),
    ('sad_rejonowy_wrzesni', 'Sąd Rejonowy we Wrześni', 'sad_okregowy_poznan', 'Września'),
    ('sad_rejonowy_zlotowie', 'Sąd Rejonowy w Złotowie', 'sad_okregowy_poznan', 'Złotów'),
    ('sad_rejonowy_jaroslawiu', 'Sąd Rejonowy w Jarosławiu', 'sad_okregowy_przemysl', 'Jarosław'),
    ('sad_rejonowy_lubaczowie', 'Sąd Rejonowy w Lubaczowie', 'sad_okregowy_przemysl', 'Lubaczów'),
    ('sad_rejonowy_przemyslu', 'Sąd Rejonowy w Przemyślu', 'sad_okregowy_przemysl', 'Przemyśl'),
    ('sad_rejonowy_przeworsku', 'Sąd Rejonowy w Przeworsku', 'sad_okregowy_przemysl', 'Przeworsk'),
    ('sad_rejonowy_grojcu', 'Sąd Rejonowy w Grójcu', 'sad_okregowy_radom', 'Grójec'),
    ('sad_rejonowy_kozienicach', 'Sąd Rejonowy w Kozienicach', 'sad_okregowy_radom', 'Kozienice'),
    ('sad_rejonowy_lipsku', 'Sąd Rejonowy w Lipsku', 'sad_okregowy_radom', 'Lipsk'),
    ('sad_rejonowy_przysusze', 'Sąd Rejonowy w Przysusze', 'sad_okregowy_radom', 'Przysucha'),
    ('sad_rejonowy_radomiu', 'Sąd Rejonowy w Radomiu', 'sad_okregowy_radom', 'Radom'),
    ('sad_rejonowy_szydlowcu', 'Sąd Rejonowy w Szydłowcu', 'sad_okregowy_radom', 'Szydłowiec'),
    ('sad_rejonowy_zwoleniu', 'Sąd Rejonowy w Zwoleniu', 'sad_okregowy_radom', 'Zwoleń'),
    ('sad_rejonowy_jastrzebiu_zdroju', 'Sąd Rejonowy w Jastrzębiu-Zdroju', 'sad_okregowy_rybnik', 'Jastrzębie-Zdrój'),
    ('sad_rejonowy_raciborzu', 'Sąd Rejonowy w Raciborzu', 'sad_okregowy_rybnik', 'Racibórz'),
    ('sad_rejonowy_rybniku', 'Sąd Rejonowy w Rybniku', 'sad_okregowy_rybnik', 'Rybnik'),
    ('sad_rejonowy_wodzislawiu_slaskim', 'Sąd Rejonowy w Wodzisławiu Śląskim', 'sad_okregowy_rybnik', 'Wodzisław Śląski'),
    ('sad_rejonowy_zorach', 'Sąd Rejonowy w Żorach', 'sad_okregowy_rybnik', 'Żory'),
    ('sad_rejonowy_debicy', 'Sąd Rejonowy w Dębicy', 'sad_okregowy_rzeszow', 'Dębica'),
    ('sad_rejonowy_lancucie', 'Sąd Rejonowy w Łańcucie', 'sad_okregowy_rzeszow', 'Łańcut'),
    ('sad_rejonowy_lezajsku', 'Sąd Rejonowy w Leżajsku', 'sad_okregowy_rzeszow', 'Leżajsk'),
    ('sad_rejonowy_ropczycach', 'Sąd Rejonowy w Ropczycach', 'sad_okregowy_rzeszow', 'Ropczyce'),
    ('sad_rejonowy_rzeszowie', 'Sąd Rejonowy w Rzeszowie', 'sad_okregowy_rzeszow', 'Rzeszów'),
    ('sad_rejonowy_strzyzowie', 'Sąd Rejonowy w Strzyżowie', 'sad_okregowy_rzeszow', 'Strzyżów'),
    ('sad_rejonowy_garwolinie', 'Sąd Rejonowy w Garwolinie', 'sad_okregowy_siedlce', 'Garwolin'),
    ('sad_rejonowy_minsku_mazowieckim', 'Sąd Rejonowy w Mińsku Mazowieckim', 'sad_okregowy_siedlce', 'Mińsk Mazowiecki'),
    ('sad_rejonowy_siedlcach', 'Sąd Rejonowy w Siedlcach', 'sad_okregowy_siedlce', 'Siedlce'),
    ('sad_rejonowy_sokolowie_podlaskim', 'Sąd Rejonowy w Sokołowie Podlaskim', 'sad_okregowy_siedlce', 'Sokołów Podlaski'),
    ('sad_rejonowy_wegrowie', 'Sąd Rejonowy w Węgrowie', 'sad_okregowy_siedlce', 'Węgrów'),
    ('sad_rejonowy_lasku', 'Sąd Rejonowy w Łasku', 'sad_okregowy_sieradz', 'Łask'),
    ('sad_rejonowy_sieradzu', 'Sąd Rejonowy w Sieradzu', 'sad_okregowy_sieradz', 'Sieradz'),
    ('sad_rejonowy_wieluniu', 'Sąd Rejonowy w Wieluniu', 'sad_okregowy_sieradz', 'Wieluń'),
    ('sad_rejonowy_zdunskiej_woli', 'Sąd Rejonowy w Zduńskiej Woli', 'sad_okregowy_sieradz', 'Zduńska Wola'),
    ('sad_rejonowy_bytowie', 'Sąd Rejonowy w Bytowie', 'sad_okregowy_slupsk', 'Bytów'),
    ('sad_rejonowy_chojnicach', 'Sąd Rejonowy w Chojnicach', 'sad_okregowy_slupsk', 'Chojnice'),
    ('sad_rejonowy_czluchowie', 'Sąd Rejonowy w Człuchowie', 'sad_okregowy_slupsk', 'Człuchów'),
    ('sad_rejonowy_leborku', 'Sąd Rejonowy w Lęborku', 'sad_okregowy_slupsk', 'Lębork'),
    ('sad_rejonowy_miastku', 'Sąd Rejonowy w Miastku', 'sad_okregowy_slupsk', 'Miastko'),
    ('sad_rejonowy_slupsku', 'Sąd Rejonowy w Słupsku', 'sad_okregowy_slupsk', 'Słupsk'),
    ('sad_rejonowy_bedzinie', 'Sąd Rejonowy w Będzinie', 'sad_okregowy_sosnowiec', 'Będzin'),
    ('sad_rejonowy_czeladz', 'Sąd Rejonowy w Czeladzi', 'sad_okregowy_sosnowiec', 'Czeladź'),
    ('sad_rejonowy_dabrowie_gorniczej', 'Sąd Rejonowy w Dąbrowie Górniczej', 'sad_okregowy_sosnowiec', 'Dąbrowa Górnicza'),
    ('sad_rejonowy_jaworznie', 'Sąd Rejonowy w Jaworznie', 'sad_okregowy_sosnowiec', 'Jaworzno'),
    ('sad_rejonowy_sosnowcu', 'Sąd Rejonowy w Sosnowcu', 'sad_okregowy_sosnowiec', 'Sosnowiec'),
    ('sad_rejonowy_zawierciu', 'Sąd Rejonowy w Zawierciu', 'sad_okregowy_sosnowiec', 'Zawiercie'),
    ('sad_rejonowy_augustowie', 'Sąd Rejonowy w Augustowie', 'sad_okregowy_suwalki', 'Augustów'),
    ('sad_rejonowy_elku', 'Sąd Rejonowy w Ełku', 'sad_okregowy_suwalki', 'Ełk'),
    ('sad_rejonowy_olecku', 'Sąd Rejonowy w Olecku', 'sad_okregowy_suwalki', 'Olecko'),
    ('sad_rejonowy_suwalkach', 'Sąd Rejonowy w Suwałkach', 'sad_okregowy_suwalki', 'Suwałki'),
    ('sad_rejonowy_dzierzoniowie', 'Sąd Rejonowy w Dzierżoniowie', 'sad_okregowy_swidnica', 'Dzierżoniów'),
    ('sad_rejonowy_klodzku', 'Sąd Rejonowy w Kłodzku', 'sad_okregowy_swidnica', 'Kłodzko'),
    ('sad_rejonowy_swidnicy', 'Sąd Rejonowy w Świdnicy', 'sad_okregowy_swidnica', 'Świdnica'),
    ('sad_rejonowy_walbrzychu', 'Sąd Rejonowy w Wałbrzychu', 'sad_okregowy_swidnica', 'Wałbrzych'),
    ('sad_rejonowy_zabkowicach_slaskich', 'Sąd Rejonowy w Ząbkowicach Śląskich', 'sad_okregowy_swidnica', 'Ząbkowice Śląskie'),
    ('sad_rejonowy_choszcznie', 'Sąd Rejonowy w Choszcznie', 'sad_okregowy_szczecin', 'Choszczno'),
    ('sad_rejonowy_goleniowie', 'Sąd Rejonowy w Goleniowie', 'sad_okregowy_szczecin', 'Goleniów'),
    ('sad_rejonowy_gryficach', 'Sąd Rejonowy w Gryficach', 'sad_okregowy_szczecin', 'Gryfice'),
    ('sad_rejonowy_gryfinie', 'Sąd Rejonowy w Gryfinie', 'sad_okregowy_szczecin', 'Gryfino'),
    ('sad_rejonowy_kamieniu_pomorskim', 'Sąd Rejonowy w Kamieniu Pomorskim', 'sad_okregowy_szczecin', 'Kamień Pomorski'),
    ('sad_rejonowy_lobzie', 'Sąd Rejonowy w Łobzie', 'sad_okregowy_szczecin', 'Łobez'),
    ('sad_rejonowy_mysliborzu', 'Sąd Rejonowy w Myśliborzu', 'sad_okregowy_szczecin', 'Myślibórz'),
    ('sad_rejonowy_stargardzie', 'Sąd Rejonowy w Stargardzie', 'sad_okregowy_szczecin', 'Stargard'),
    ('sad_rejonowy_swinoujsciu', 'Sąd Rejonowy w Świnoujściu', 'sad_okregowy_szczecin', 'Świnoujście'),
    ('sad_rejonowy_szczecin_centrum', 'Sąd Rejonowy Szczecin-Centrum w Szczecinie', 'sad_okregowy_szczecin', 'Szczecin'),
    ('sad_rejonowy_szczecin_prawobrzeze_i_zachod', 'Sąd Rejonowy Szczecin-Prawobrzeże i Zachód w Szczecinie', 'sad_okregowy_szczecin', 'Szczecin'),
    ('sad_rejonowy_kolbuszowej', 'Sąd Rejonowy w Kolbuszowej', 'sad_okregowy_tarnobrzeg', 'Kolbuszowa'),
    ('sad_rejonowy_mielcu', 'Sąd Rejonowy w Mielcu', 'sad_okregowy_tarnobrzeg', 'Mielec'),
    ('sad_rejonowy_nisku', 'Sąd Rejonowy w Nisku', 'sad_okregowy_tarnobrzeg', 'Nisk'),
    ('sad_rejonowy_stalowej_woli', 'Sąd Rejonowy w Stalowej Woli', 'sad_okregowy_tarnobrzeg', 'Stalowa Wola'),
    ('sad_rejonowy_tarnobrzegu', 'Sąd Rejonowy w Tarnobrzegu', 'sad_okregowy_tarnobrzeg', 'Tarnobrzeg'),
    ('sad_rejonowy_bochni', 'Sąd Rejonowy w Bochni', 'sad_okregowy_tarnow', 'Bochnia'),
    ('sad_rejonowy_brzesku', 'Sąd Rejonowy w Brzesku', 'sad_okregowy_tarnow', 'Brzesk'),
    ('sad_rejonowy_dabrowie_tarnowskiej', 'Sąd Rejonowy w Dąbrowie Tarnowskiej', 'sad_okregowy_tarnow', 'Dąbrowa Tarnowska'),
    ('sad_rejonowy_tarnowie', 'Sąd Rejonowy w Tarnowie', 'sad_okregowy_tarnow', 'Tarnów'),
    ('sad_rejonowy_brodnicy', 'Sąd Rejonowy w Brodnicy', 'sad_okregowy_torun', 'Brodnica'),
    ('sad_rejonowy_chelmnie', 'Sąd Rejonowy w Chełmnie', 'sad_okregowy_torun', 'Chełmno'),
    ('sad_rejonowy_golubiu_dobrzyniu', 'Sąd Rejonowy w Golubiu-Dobrzyniu', 'sad_okregowy_torun', 'Golubiu-Dobrzyń'),
    ('sad_rejonowy_grudziadzu', 'Sąd Rejonowy w Grudziądzu', 'sad_okregowy_torun', 'Grudziądz'),
    ('sad_rejonowy_toruniu', 'Sąd Rejonowy w Toruniu', 'sad_okregowy_torun', 'Toruń'),
    ('sad_rejonowy_wabrzeznie', 'Sąd Rejonowy w Wąbrzeźnie', 'sad_okregowy_torun', 'Wąbrzeźno'),
    ('sad_rejonowy_grodzisku_mazowieckim', 'Sąd Rejonowy w Grodzisku Mazowieckim', 'sad_okregowy_warszawa', 'Grodzisk Mazowiecki'),
    ('sad_rejonowy_piasecznie', 'Sąd Rejonowy w Piasecznie', 'sad_okregowy_warszawa', 'Piaseczno'),
    ('sad_rejonowy_pruszkowie', 'Sąd Rejonowy w Pruszkowie', 'sad_okregowy_warszawa', 'Pruszków'),
    ('sad_rejonowy_warszawa_miasto_stoleczne', 'Sąd Rejonowy dla miasta stołecznego Warszawy w Warszawie', 'sad_okregowy_warszawa', 'Warszawa'),
    ('sad_rejonowy_warszawy_mokotowa', 'Sąd Rejonowy dla Warszawy-Mokotowa w Warszawie', 'sad_okregowy_warszawa', 'Warszawa'),
    ('sad_rejonowy_warszawy_srodmiescia', 'Sąd Rejonowy dla Warszawy-Śródmieścia w Warszawie', 'sad_okregowy_warszawa', 'Warszawa'),
    ('sad_rejonowy_warszawy_woli', 'Sąd Rejonowy dla Warszawy-Woli w Warszawie', 'sad_okregowy_warszawa', 'Warszawa'),
    ('sad_rejonowy_warszawy_zoliborza', 'Sąd Rejonowy dla Warszawy-Żoliborza w Warszawie', 'sad_okregowy_warszawa', 'Warszawa'),
    ('sad_rejonowy_legionowie', 'Sąd Rejonowy w Legionowie', 'sad_okregowy_warszawa_praga', 'Legionów'),
    ('sad_rejonowy_nowym_dworze_mazowieckim', 'Sąd Rejonowy w Nowym Dworze Mazowieckim', 'sad_okregowy_warszawa_praga', 'Nowy Dwór Mazowiecki'),
    ('sad_rejonowy_otwocku', 'Sąd Rejonowy w Otwocku', 'sad_okregowy_warszawa_praga', 'Otwock'),
    ('sad_rejonowy_warszawy_pragi_polnoc', 'Sąd Rejonowy dla Warszawy Pragi-Północ w Warszawie', 'sad_okregowy_warszawa_praga', 'Warszawa'),
    ('sad_rejonowy_warszawy_pragi_poludnie', 'Sąd Rejonowy dla Warszawy Pragi-Południe w Warszawie', 'sad_okregowy_warszawa_praga', 'Warszawa'),
    ('sad_rejonowy_wolominie', 'Sąd Rejonowy w Wołominie', 'sad_okregowy_warszawa_praga', 'Wołomin'),
    ('sad_rejonowy_aleksandrowie_kujawskim', 'Sąd Rejonowy w Aleksandrowie Kujawskim', 'sad_okregowy_wloclawek', 'Aleksandrów Kujawski'),
    ('sad_rejonowy_lipnie', 'Sąd Rejonowy w Lipnie', 'sad_okregowy_wloclawek', 'Lipno'),
    ('sad_rejonowy_radziejowie', 'Sąd Rejonowy w Radziejowie', 'sad_okregowy_wloclawek', 'Radziejów'),
    ('sad_rejonowy_rypinie', 'Sąd Rejonowy w Rypinie', 'sad_okregowy_wloclawek', 'Rypin'),
    ('sad_rejonowy_wloclawku', 'Sąd Rejonowy we Włocławku', 'sad_okregowy_wloclawek', 'Włocławek'),
    ('sad_rejonowy_miliczu', 'Sąd Rejonowy w Miliczu', 'sad_okregowy_wroclaw', 'Milicz'),
    ('sad_rejonowy_olawie', 'Sąd Rejonowy w Oławie', 'sad_okregowy_wroclaw', 'Oława'),
    ('sad_rejonowy_olesnicy', 'Sąd Rejonowy w Oleśnicy', 'sad_okregowy_wroclaw', 'Oleśnica'),
    ('sad_rejonowy_srodzie_slaskiej', 'Sąd Rejonowy w Środzie Śląskiej', 'sad_okregowy_wroclaw', 'Środa Śląska'),
    ('sad_rejonowy_strzelinie', 'Sąd Rejonowy w Strzelinie', 'sad_okregowy_wroclaw', 'Strzelin'),
    ('sad_rejonowy_trzebnicy', 'Sąd Rejonowy w Trzebnicy', 'sad_okregowy_wroclaw', 'Trzebnica'),
    ('sad_rejonowy_wolowie', 'Sąd Rejonowy w Wołowie', 'sad_okregowy_wroclaw', 'Wołów'),
    ('sad_rejonowy_wroclawia_fabrycznej', 'Sąd Rejonowy dla Wrocławia-Fabrycznej we Wrocławiu', 'sad_okregowy_wroclaw', 'Wrocław'),
    ('sad_rejonowy_wroclawia_krzykow', 'Sąd Rejonowy dla Wrocławia-Krzyków we Wrocławiu', 'sad_okregowy_wroclaw', 'Wrocław'),
    ('sad_rejonowy_wroclawia_srodmiescia', 'Sąd Rejonowy dla Wrocławia-Śródmieścia we Wrocławiu', 'sad_okregowy_wroclaw', 'Wrocław'),
    ('sad_rejonowy_bilgoraju', 'Sąd Rejonowy w Biłgoraju', 'sad_okregowy_zamosc', 'Biłgoraj'),
    ('sad_rejonowy_hrubieszowie', 'Sąd Rejonowy w Hrubieszowie', 'sad_okregowy_zamosc', 'Hrubieszów'),
    ('sad_rejonowy_janowie_lubelskim', 'Sąd Rejonowy w Janowie Lubelskim', 'sad_okregowy_zamosc', 'Janów Lubelski'),
    ('sad_rejonowy_krasnymstawie', 'Sąd Rejonowy w Krasnymstawie', 'sad_okregowy_zamosc', 'Krasnystaw'),
    ('sad_rejonowy_tomaszowie_lubelskim', 'Sąd Rejonowy w Tomaszowie Lubelskim', 'sad_okregowy_zamosc', 'Tomaszów Lubelski'),
    ('sad_rejonowy_zamosciu', 'Sąd Rejonowy w Zamościu', 'sad_okregowy_zamosc', 'Zamość'),
    ('sad_rejonowy_krosnie_odrzanskim', 'Sąd Rejonowy w Krośnie Odrzańskim', 'sad_okregowy_zielona_gora', 'Krosno Odrzańskie'),
    ('sad_rejonowy_nowej_soli', 'Sąd Rejonowy w Nowej Soli', 'sad_okregowy_zielona_gora', 'Nowa Sól'),
    ('sad_rejonowy_swiebodzinie', 'Sąd Rejonowy w Świebodzinie', 'sad_okregowy_zielona_gora', 'Świebodzin'),
    ('sad_rejonowy_wschowie', 'Sąd Rejonowy we Wschowie', 'sad_okregowy_zielona_gora', 'Wschów'),
    ('sad_rejonowy_zaganiu', 'Sąd Rejonowy w Żaganiu', 'sad_okregowy_zielona_gora', 'Żagań'),
    ('sad_rejonowy_zarach', 'Sąd Rejonowy w Żarach', 'sad_okregowy_zielona_gora', 'Żary'),
    ('sad_rejonowy_zielonej_gorze', 'Sąd Rejonowy w Zielonej Górze', 'sad_okregowy_zielona_gora', 'Zielona Góra');

-- 3. Populate courts.courts (319 regional courts, grouped by district)
DO $$
DECLARE
    v_parent_id UUID;
BEGIN

    -- sad_okregowy_bialystok (3 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_bialystok';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_bialymstoku', v_parent_id, 'Sąd Rejonowy w Białymstoku', 'Białystok'),
        ('regional', 'sad_rejonowy_bielsku_podlaskim', v_parent_id, 'Sąd Rejonowy w Bielsku Podlaskim', 'Bielsk Podlaski'),
        ('regional', 'sad_rejonowy_sokolce', v_parent_id, 'Sąd Rejonowy w Sokółce', 'Sokółka');

    -- sad_okregowy_bielsko_biala (3 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_bielsko_biala';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_bielsku_bialej', v_parent_id, 'Sąd Rejonowy w Bielsku-Białej', 'Bielsko-Biała'),
        ('regional', 'sad_rejonowy_cieszynie', v_parent_id, 'Sąd Rejonowy w Cieszynie', 'Cieszyn'),
        ('regional', 'sad_rejonowy_zywcu', v_parent_id, 'Sąd Rejonowy w Żywcu', 'Żywiec');

    -- sad_okregowy_bydgoszcz (8 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_bydgoszcz';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_bydgoszczy', v_parent_id, 'Sąd Rejonowy w Bydgoszczy', 'Bydgoszcz'),
        ('regional', 'sad_rejonowy_inowroclawiu', v_parent_id, 'Sąd Rejonowy w Inowrocławiu', 'Inowrocław'),
        ('regional', 'sad_rejonowy_mogilnie', v_parent_id, 'Sąd Rejonowy w Mogilnie', 'Mogilno'),
        ('regional', 'sad_rejonowy_nakle_nad_notecia', v_parent_id, 'Sąd Rejonowy w Nakle nad Notecią', 'Nakło nad Notecią'),
        ('regional', 'sad_rejonowy_swieciu', v_parent_id, 'Sąd Rejonowy w Świeciu', 'Świecie'),
        ('regional', 'sad_rejonowy_szubinie', v_parent_id, 'Sąd Rejonowy w Szubinie', 'Szubin'),
        ('regional', 'sad_rejonowy_tucholi', v_parent_id, 'Sąd Rejonowy w Tucholi', 'Tuchola'),
        ('regional', 'sad_rejonowy_zninie', v_parent_id, 'Sąd Rejonowy w Żninie', 'Żnin');

    -- sad_okregowy_czestochowa (3 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_czestochowa';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_czestochowie', v_parent_id, 'Sąd Rejonowy w Częstochowie', 'Częstochowa'),
        ('regional', 'sad_rejonowy_lublincu', v_parent_id, 'Sąd Rejonowy w Lublińcu', 'Lubliniec'),
        ('regional', 'sad_rejonowy_myszkowie', v_parent_id, 'Sąd Rejonowy w Myszkowie', 'Myszków');

    -- sad_okregowy_elblag (6 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_elblag';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_braniewie', v_parent_id, 'Sąd Rejonowy w Braniewie', 'Braniewo'),
        ('regional', 'sad_rejonowy_dzialdowie', v_parent_id, 'Sąd Rejonowy w Działdowie', 'Działdów'),
        ('regional', 'sad_rejonowy_elblagu', v_parent_id, 'Sąd Rejonowy w Elblągu', 'Elbląg'),
        ('regional', 'sad_rejonowy_ilawie', v_parent_id, 'Sąd Rejonowy w Iławie', 'Iława'),
        ('regional', 'sad_rejonowy_nowym_miescie_lubawskim', v_parent_id, 'Sąd Rejonowy w Nowym Mieście Lubawskim', 'Nowe Miasto Lubawskie'),
        ('regional', 'sad_rejonowy_ostrodzie', v_parent_id, 'Sąd Rejonowy w Ostródzie', 'Ostród');

    -- sad_okregowy_gdansk (11 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_gdansk';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_gdansk_polnoc', v_parent_id, 'Sąd Rejonowy Gdańsk-Północ w Gdańsku', 'Gdańsk'),
        ('regional', 'sad_rejonowy_gdansk_poludnie', v_parent_id, 'Sąd Rejonowy Gdańsk-Południe w Gdańsku', 'Gdańsk'),
        ('regional', 'sad_rejonowy_gdyni', v_parent_id, 'Sąd Rejonowy w Gdyni', 'Gdynia'),
        ('regional', 'sad_rejonowy_kartuzach', v_parent_id, 'Sąd Rejonowy w Kartuzach', 'Kartuzy'),
        ('regional', 'sad_rejonowy_koscierzynie', v_parent_id, 'Sąd Rejonowy w Kościerzynie', 'Kościerzyna'),
        ('regional', 'sad_rejonowy_kwidzynie', v_parent_id, 'Sąd Rejonowy w Kwidzynie', 'Kwidzyn'),
        ('regional', 'sad_rejonowy_malborku', v_parent_id, 'Sąd Rejonowy w Malborku', 'Malbork'),
        ('regional', 'sad_rejonowy_sopocie', v_parent_id, 'Sąd Rejonowy w Sopocie', 'Sopot'),
        ('regional', 'sad_rejonowy_starogardzie_gdanskim', v_parent_id, 'Sąd Rejonowy w Starogardzie Gdańskim', 'Starogard Gdański'),
        ('regional', 'sad_rejonowy_tczewie', v_parent_id, 'Sąd Rejonowy w Tczewie', 'Tczew'),
        ('regional', 'sad_rejonowy_wejherowie', v_parent_id, 'Sąd Rejonowy w Wejherowie', 'Wejherów');

    -- sad_okregowy_gliwice (4 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_gliwice';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_gliwicach', v_parent_id, 'Sąd Rejonowy w Gliwicach', 'Gliwice'),
        ('regional', 'sad_rejonowy_rudzie_slaskiej', v_parent_id, 'Sąd Rejonowy w Rudzie Śląskiej', 'Ruda Śląska'),
        ('regional', 'sad_rejonowy_tarnowskich_gorach', v_parent_id, 'Sąd Rejonowy w Tarnowskich Górach', 'Tarnowskie Góry'),
        ('regional', 'sad_rejonowy_zabrzu', v_parent_id, 'Sąd Rejonowy w Zabrzu', 'Zabrze');

    -- sad_okregowy_gorzow_wielkopolski (5 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_gorzow_wielkopolski';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_gorzowie_wielkopolskim', v_parent_id, 'Sąd Rejonowy w Gorzowie Wielkopolskim', 'Gorzów Wielkopolski'),
        ('regional', 'sad_rejonowy_miedzyrzeczu', v_parent_id, 'Sąd Rejonowy w Międzyrzeczu', 'Międzyrzecz'),
        ('regional', 'sad_rejonowy_slubicach', v_parent_id, 'Sąd Rejonowy w Słubicach', 'Słubice'),
        ('regional', 'sad_rejonowy_strzelcach_krajenskich', v_parent_id, 'Sąd Rejonowy w Strzelcach Krajeńskich', 'Strzelce Krajeńskie'),
        ('regional', 'sad_rejonowy_sulecinie', v_parent_id, 'Sąd Rejonowy w Sulęcinie', 'Sulęcin');

    -- sad_okregowy_jelenia_gora (6 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_jelenia_gora';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_boleslawcu', v_parent_id, 'Sąd Rejonowy w Bolesławcu', 'Bolesławiec'),
        ('regional', 'sad_rejonowy_jeleniej_gorze', v_parent_id, 'Sąd Rejonowy w Jeleniej Górze', 'Jelenia Góra'),
        ('regional', 'sad_rejonowy_kamiennej_gorze', v_parent_id, 'Sąd Rejonowy w Kamiennej Górze', 'Kamienna Góra'),
        ('regional', 'sad_rejonowy_lubaniu', v_parent_id, 'Sąd Rejonowy w Lubaniu', 'Lubań'),
        ('regional', 'sad_rejonowy_lwowku_slaskim', v_parent_id, 'Sąd Rejonowy w Lwówku Śląskim', 'Lwówek Śląski'),
        ('regional', 'sad_rejonowy_zgorzelcu', v_parent_id, 'Sąd Rejonowy w Zgorzelcu', 'Zgorzelec');

    -- sad_okregowy_kalisz (7 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_kalisz';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_jarocinie', v_parent_id, 'Sąd Rejonowy w Jarocinie', 'Jarocin'),
        ('regional', 'sad_rejonowy_kaliszu', v_parent_id, 'Sąd Rejonowy w Kaliszu', 'Kalisz'),
        ('regional', 'sad_rejonowy_kepnie', v_parent_id, 'Sąd Rejonowy w Kępnie', 'Kępno'),
        ('regional', 'sad_rejonowy_krotoszynie', v_parent_id, 'Sąd Rejonowy w Krotoszynie', 'Krotoszyn'),
        ('regional', 'sad_rejonowy_ostrowie_wielkopolskim', v_parent_id, 'Sąd Rejonowy w Ostrowie Wielkopolskim', 'Ostrów Wielkopolski'),
        ('regional', 'sad_rejonowy_ostrzeszowie', v_parent_id, 'Sąd Rejonowy w Ostrzeszowie', 'Ostrzeszów'),
        ('regional', 'sad_rejonowy_pleszewie', v_parent_id, 'Sąd Rejonowy w Pleszewie', 'Pleszew');

    -- sad_okregowy_katowice (9 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_katowice';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_bytomiu', v_parent_id, 'Sąd Rejonowy w Bytomiu', 'Bytom'),
        ('regional', 'sad_rejonowy_chorzowie', v_parent_id, 'Sąd Rejonowy w Chorzowie', 'Chorzów'),
        ('regional', 'sad_rejonowy_katowice_wschod', v_parent_id, 'Sąd Rejonowy Katowice-Wschód w Katowicach', 'Katowice'),
        ('regional', 'sad_rejonowy_katowice_zachod', v_parent_id, 'Sąd Rejonowy Katowice-Zachód w Katowicach', 'Katowice'),
        ('regional', 'sad_rejonowy_mikolowie', v_parent_id, 'Sąd Rejonowy w Mikołowie', 'Mikołów'),
        ('regional', 'sad_rejonowy_myslowicach', v_parent_id, 'Sąd Rejonowy w Mysłowicach', 'Mysłowice'),
        ('regional', 'sad_rejonowy_pszczynie', v_parent_id, 'Sąd Rejonowy w Pszczynie', 'Pszczyna'),
        ('regional', 'sad_rejonowy_siemianowicach_slaskich', v_parent_id, 'Sąd Rejonowy w Siemianowicach Śląskich', 'Siemianowice Śląskie'),
        ('regional', 'sad_rejonowy_tychach', v_parent_id, 'Sąd Rejonowy w Tychach', 'Tychy');

    -- sad_okregowy_kielce (12 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_kielce';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_busku_zdroju', v_parent_id, 'Sąd Rejonowy w Busku-Zdroju', 'Busko-Zdrój'),
        ('regional', 'sad_rejonowy_jedrzejowie', v_parent_id, 'Sąd Rejonowy w Jędrzejowie', 'Jędrzejów'),
        ('regional', 'sad_rejonowy_kielcach', v_parent_id, 'Sąd Rejonowy w Kielcach', 'Kielce'),
        ('regional', 'sad_rejonowy_konskich', v_parent_id, 'Sąd Rejonowy w Końskich', 'Końskie'),
        ('regional', 'sad_rejonowy_opatowie', v_parent_id, 'Sąd Rejonowy w Opatowie', 'Opatów'),
        ('regional', 'sad_rejonowy_ostrowcu_swietokrzyskim', v_parent_id, 'Sąd Rejonowy w Ostrowcu Świętokrzyskim', 'Ostrowiec Świętokrzyski'),
        ('regional', 'sad_rejonowy_pinczowie', v_parent_id, 'Sąd Rejonowy w Pińczowie', 'Pińczów'),
        ('regional', 'sad_rejonowy_sandomierzu', v_parent_id, 'Sąd Rejonowy w Sandomierzu', 'Sandomierz'),
        ('regional', 'sad_rejonowy_skarzysku_kamiennej', v_parent_id, 'Sąd Rejonowy w Skarżysku-Kamiennej', 'Skarżysko-Kamienna'),
        ('regional', 'sad_rejonowy_starachowicach', v_parent_id, 'Sąd Rejonowy w Starachowicach', 'Starachowice'),
        ('regional', 'sad_rejonowy_staszowie', v_parent_id, 'Sąd Rejonowy w Staszowie', 'Staszów'),
        ('regional', 'sad_rejonowy_wloszczowie', v_parent_id, 'Sąd Rejonowy we Włoszczowie', 'Włoszczów');

    -- sad_okregowy_konin (4 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_konin';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_kole', v_parent_id, 'Sąd Rejonowy w Kole', 'Koło'),
        ('regional', 'sad_rejonowy_koninie', v_parent_id, 'Sąd Rejonowy w Koninie', 'Konin'),
        ('regional', 'sad_rejonowy_slupcy', v_parent_id, 'Sąd Rejonowy w Słupcy', 'Słupca'),
        ('regional', 'sad_rejonowy_turku', v_parent_id, 'Sąd Rejonowy w Turku', 'Turek');

    -- sad_okregowy_koszalin (7 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_koszalin';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_bialogardzie', v_parent_id, 'Sąd Rejonowy w Białogardzie', 'Białogard'),
        ('regional', 'sad_rejonowy_drawsku_pomorskim', v_parent_id, 'Sąd Rejonowy w Drawsku Pomorskim', 'Drawsko Pomorskie'),
        ('regional', 'sad_rejonowy_kolobrzegu', v_parent_id, 'Sąd Rejonowy w Kołobrzegu', 'Kołobrzeg'),
        ('regional', 'sad_rejonowy_koszalinie', v_parent_id, 'Sąd Rejonowy w Koszalinie', 'Koszalin'),
        ('regional', 'sad_rejonowy_slawnie', v_parent_id, 'Sąd Rejonowy w Sławnie', 'Sławno'),
        ('regional', 'sad_rejonowy_szczecinku', v_parent_id, 'Sąd Rejonowy w Szczecinku', 'Szczecinek'),
        ('regional', 'sad_rejonowy_walczu', v_parent_id, 'Sąd Rejonowy w Wałczu', 'Wałcz');

    -- sad_okregowy_krakow (12 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_krakow';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_chrzanowie', v_parent_id, 'Sąd Rejonowy w Chrzanowie', 'Chrzanów'),
        ('regional', 'sad_rejonowy_krakowa_krowodrzy', v_parent_id, 'Sąd Rejonowy dla Krakowa-Krowodrzy w Krakowie', 'Kraków'),
        ('regional', 'sad_rejonowy_krakowa_nowej_huty', v_parent_id, 'Sąd Rejonowy dla Krakowa-Nowej Huty w Krakowie', 'Kraków'),
        ('regional', 'sad_rejonowy_krakowa_podgorza', v_parent_id, 'Sąd Rejonowy dla Krakowa-Podgórza w Krakowie', 'Kraków'),
        ('regional', 'sad_rejonowy_krakowa_srodmiescia', v_parent_id, 'Sąd Rejonowy dla Krakowa-Śródmieścia w Krakowie', 'Kraków'),
        ('regional', 'sad_rejonowy_miechowie', v_parent_id, 'Sąd Rejonowy w Miechowie', 'Miechów'),
        ('regional', 'sad_rejonowy_myslenicach', v_parent_id, 'Sąd Rejonowy w Myślenicach', 'Myślenice'),
        ('regional', 'sad_rejonowy_olkuszu', v_parent_id, 'Sąd Rejonowy w Olkuszu', 'Olkusz'),
        ('regional', 'sad_rejonowy_oswiecimiu', v_parent_id, 'Sąd Rejonowy w Oświęcimiu', 'Oświęcim'),
        ('regional', 'sad_rejonowy_suchej_beskidzkiej', v_parent_id, 'Sąd Rejonowy w Suchej Beskidzkiej', 'Sucha Beskidzka'),
        ('regional', 'sad_rejonowy_wadowicach', v_parent_id, 'Sąd Rejonowy w Wadowicach', 'Wadowice'),
        ('regional', 'sad_rejonowy_wieliczce', v_parent_id, 'Sąd Rejonowy w Wieliczce', 'Wieliczka');

    -- sad_okregowy_krosno (5 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_krosno';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_brzozowie', v_parent_id, 'Sąd Rejonowy w Brzozowie', 'Brzozów'),
        ('regional', 'sad_rejonowy_jasle', v_parent_id, 'Sąd Rejonowy w Jaśle', 'Jasło'),
        ('regional', 'sad_rejonowy_krosnie', v_parent_id, 'Sąd Rejonowy w Krośnie', 'Krosno'),
        ('regional', 'sad_rejonowy_lesku', v_parent_id, 'Sąd Rejonowy w Lesku', 'Lesk'),
        ('regional', 'sad_rejonowy_sanoku', v_parent_id, 'Sąd Rejonowy w Sanoku', 'Sanok');

    -- sad_okregowy_legnica (5 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_legnica';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_glogowie', v_parent_id, 'Sąd Rejonowy w Głogowie', 'Głogów'),
        ('regional', 'sad_rejonowy_jaworze', v_parent_id, 'Sąd Rejonowy w Jaworze', 'Jawor'),
        ('regional', 'sad_rejonowy_legnicy', v_parent_id, 'Sąd Rejonowy w Legnicy', 'Legnica'),
        ('regional', 'sad_rejonowy_lubinie', v_parent_id, 'Sąd Rejonowy w Lubinie', 'Lubin'),
        ('regional', 'sad_rejonowy_zlotoryi', v_parent_id, 'Sąd Rejonowy w Złotoryi', 'Złotoryja');

    -- sad_okregowy_lodz (10 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_lodz';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_brzezinach', v_parent_id, 'Sąd Rejonowy w Brzezinach', 'Brzeziny'),
        ('regional', 'sad_rejonowy_kutnie', v_parent_id, 'Sąd Rejonowy w Kutnie', 'Kutno'),
        ('regional', 'sad_rejonowy_leczycy', v_parent_id, 'Sąd Rejonowy w Łęczycy', 'Łęczyca'),
        ('regional', 'sad_rejonowy_lodzi_srodmiescia', v_parent_id, 'Sąd Rejonowy dla Łodzi-Śródmieścia w Łodzi', 'Łódź'),
        ('regional', 'sad_rejonowy_lodzi_widzewa', v_parent_id, 'Sąd Rejonowy dla Łodzi-Widzewa w Łodzi', 'Łódź'),
        ('regional', 'sad_rejonowy_lowiczu', v_parent_id, 'Sąd Rejonowy w Łowiczu', 'Łowicz'),
        ('regional', 'sad_rejonowy_pabianicach', v_parent_id, 'Sąd Rejonowy w Pabianicach', 'Pabianice'),
        ('regional', 'sad_rejonowy_rawie_mazowieckiej', v_parent_id, 'Sąd Rejonowy w Rawie Mazowieckiej', 'Rawa Mazowiecka'),
        ('regional', 'sad_rejonowy_skierniewicach', v_parent_id, 'Sąd Rejonowy w Skierniewicach', 'Skierniewice'),
        ('regional', 'sad_rejonowy_zgierzu', v_parent_id, 'Sąd Rejonowy w Zgierzu', 'Zgierz');

    -- sad_okregowy_lomza (4 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_lomza';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_grajewie', v_parent_id, 'Sąd Rejonowy w Grajewie', 'Grajewo'),
        ('regional', 'sad_rejonowy_lomzy', v_parent_id, 'Sąd Rejonowy w Łomży', 'Łomża'),
        ('regional', 'sad_rejonowy_wysokiem_mazowieckiem', v_parent_id, 'Sąd Rejonowy w Wysokiem Mazowieckiem', 'Wysokie Mazowieckie'),
        ('regional', 'sad_rejonowy_zambrowie', v_parent_id, 'Sąd Rejonowy w Zambrowie', 'Zambrów');

    -- sad_okregowy_lublin (12 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_lublin';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_bialej_podlaskiej', v_parent_id, 'Sąd Rejonowy w Białej Podlaskiej', 'Biała Podlaska'),
        ('regional', 'sad_rejonowy_chelmie', v_parent_id, 'Sąd Rejonowy w Chełmie', 'Chełm'),
        ('regional', 'sad_rejonowy_krasniku', v_parent_id, 'Sąd Rejonowy w Kraśniku', 'Kraśnik'),
        ('regional', 'sad_rejonowy_lubartowie', v_parent_id, 'Sąd Rejonowy w Lubartowie', 'Lubartów'),
        ('regional', 'sad_rejonowy_lublin_wschod', v_parent_id, 'Sąd Rejonowy Lublin-Wschód w Lublinie z siedzibą w Świdniku', 'Świdnik'),
        ('regional', 'sad_rejonowy_lublin_zachod', v_parent_id, 'Sąd Rejonowy Lublin-Zachód w Lublinie', 'Lublin'),
        ('regional', 'sad_rejonowy_lukowie', v_parent_id, 'Sąd Rejonowy w Łukowie', 'Łuków'),
        ('regional', 'sad_rejonowy_opolu_lubelskim', v_parent_id, 'Sąd Rejonowy w Opolu Lubelskim', 'Opole Lubelskie'),
        ('regional', 'sad_rejonowy_pulawach', v_parent_id, 'Sąd Rejonowy w Puławach', 'Puławy'),
        ('regional', 'sad_rejonowy_radzyniu_podlaskim', v_parent_id, 'Sąd Rejonowy w Radzyniu Podlaskim', 'Radzyń Podlaski'),
        ('regional', 'sad_rejonowy_rykach', v_parent_id, 'Sąd Rejonowy w Rykach', 'Ryki'),
        ('regional', 'sad_rejonowy_wlodawie', v_parent_id, 'Sąd Rejonowy we Włodawie', 'Włodawa');

    -- sad_okregowy_nowy_sacz (5 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_nowy_sacz';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_gorlicach', v_parent_id, 'Sąd Rejonowy w Gorlicach', 'Gorlice'),
        ('regional', 'sad_rejonowy_limanowej', v_parent_id, 'Sąd Rejonowy w Limanowej', 'Limanowa'),
        ('regional', 'sad_rejonowy_nowym_saczu', v_parent_id, 'Sąd Rejonowy w Nowym Sączu', 'Nowy Sącz'),
        ('regional', 'sad_rejonowy_nowym_targu', v_parent_id, 'Sąd Rejonowy w Nowym Targu', 'Nowy Targ'),
        ('regional', 'sad_rejonowy_zakopanem', v_parent_id, 'Sąd Rejonowy w Zakopanem', 'Zakopane');

    -- sad_okregowy_olsztyn (10 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_olsztyn';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_bartoszycach', v_parent_id, 'Sąd Rejonowy w Bartoszycach', 'Bartoszyce'),
        ('regional', 'sad_rejonowy_biskupcu', v_parent_id, 'Sąd Rejonowy w Biskupcu', 'Biskupiec'),
        ('regional', 'sad_rejonowy_gizycku', v_parent_id, 'Sąd Rejonowy w Giżycku', 'Giżycko'),
        ('regional', 'sad_rejonowy_ketrzynie', v_parent_id, 'Sąd Rejonowy w Kętrzynie', 'Kętrzyn'),
        ('regional', 'sad_rejonowy_lidzbarku_warminskim', v_parent_id, 'Sąd Rejonowy w Lidzbarku Warmińskim', 'Lidzbark Warmiński'),
        ('regional', 'sad_rejonowy_mragowie', v_parent_id, 'Sąd Rejonowy w Mrągowie', 'Mrągów'),
        ('regional', 'sad_rejonowy_nidzicy', v_parent_id, 'Sąd Rejonowy w Nidzicy', 'Nidzica'),
        ('regional', 'sad_rejonowy_olsztynie', v_parent_id, 'Sąd Rejonowy w Olsztynie', 'Olsztyn'),
        ('regional', 'sad_rejonowy_piszu', v_parent_id, 'Sąd Rejonowy w Piszu', 'Pisz'),
        ('regional', 'sad_rejonowy_szczytnie', v_parent_id, 'Sąd Rejonowy w Szczytnie', 'Szczytno');

    -- sad_okregowy_opole (9 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_opole';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_brzegu', v_parent_id, 'Sąd Rejonowy w Brzegu', 'Brzeg'),
        ('regional', 'sad_rejonowy_glubczycach', v_parent_id, 'Sąd Rejonowy w Głubczycach', 'Głubczyce'),
        ('regional', 'sad_rejonowy_kedzierzynie_kozlu', v_parent_id, 'Sąd Rejonowy w Kędzierzynie-Koźlu', 'Kędzierzyn-Koźle'),
        ('regional', 'sad_rejonowy_kluczborku', v_parent_id, 'Sąd Rejonowy w Kluczborku', 'Kluczbork'),
        ('regional', 'sad_rejonowy_nysie', v_parent_id, 'Sąd Rejonowy w Nysie', 'Nysa'),
        ('regional', 'sad_rejonowy_olesnie', v_parent_id, 'Sąd Rejonowy w Oleśnie', 'Oleśno'),
        ('regional', 'sad_rejonowy_opolu', v_parent_id, 'Sąd Rejonowy w Opolu', 'Opole'),
        ('regional', 'sad_rejonowy_prudniku', v_parent_id, 'Sąd Rejonowy w Prudniku', 'Prudnik'),
        ('regional', 'sad_rejonowy_strzelcach_opolskich', v_parent_id, 'Sąd Rejonowy w Strzelcach Opolskich', 'Strzelce Opolskie');

    -- sad_okregowy_ostroleka (5 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_ostroleka';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_ostrolece', v_parent_id, 'Sąd Rejonowy w Ostrołęce', 'Ostrołęka'),
        ('regional', 'sad_rejonowy_ostrowi_mazowieckiej', v_parent_id, 'Sąd Rejonowy w Ostrowi Mazowieckiej', 'Ostrów Mazowiecka'),
        ('regional', 'sad_rejonowy_przasnyszu', v_parent_id, 'Sąd Rejonowy w Przasnyszu', 'Przasnysz'),
        ('regional', 'sad_rejonowy_pultusku', v_parent_id, 'Sąd Rejonowy w Pułtusku', 'Pułtusk'),
        ('regional', 'sad_rejonowy_wyszkowie', v_parent_id, 'Sąd Rejonowy w Wyszkowie', 'Wyszków');

    -- sad_okregowy_piotrkow_trybunalski (5 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_piotrkow_trybunalski';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_belchatowie', v_parent_id, 'Sąd Rejonowy w Bełchatowie', 'Bełchatów'),
        ('regional', 'sad_rejonowy_opocznie', v_parent_id, 'Sąd Rejonowy w Opocznie', 'Opoczno'),
        ('regional', 'sad_rejonowy_piotrkowie_trybunalskim', v_parent_id, 'Sąd Rejonowy w Piotrkowie Trybunalskim', 'Piotrków Trybunalski'),
        ('regional', 'sad_rejonowy_radomsku', v_parent_id, 'Sąd Rejonowy w Radomsku', 'Radomsk'),
        ('regional', 'sad_rejonowy_tomaszowie_mazowieckim', v_parent_id, 'Sąd Rejonowy w Tomaszowie Mazowieckim', 'Tomaszów Mazowiecki');

    -- sad_okregowy_plock (8 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_plock';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_ciechanowie', v_parent_id, 'Sąd Rejonowy w Ciechanowie', 'Ciechanów'),
        ('regional', 'sad_rejonowy_gostyninie', v_parent_id, 'Sąd Rejonowy w Gostyninie', 'Gostynin'),
        ('regional', 'sad_rejonowy_mlawie', v_parent_id, 'Sąd Rejonowy w Mławie', 'Mława'),
        ('regional', 'sad_rejonowy_plocku', v_parent_id, 'Sąd Rejonowy w Płocku', 'Płock'),
        ('regional', 'sad_rejonowy_plonsku', v_parent_id, 'Sąd Rejonowy w Płońsku', 'Płońsk'),
        ('regional', 'sad_rejonowy_sierpcu', v_parent_id, 'Sąd Rejonowy w Sierpcu', 'Sierpc'),
        ('regional', 'sad_rejonowy_sochaczewie', v_parent_id, 'Sąd Rejonowy w Sochaczewie', 'Sochaczew'),
        ('regional', 'sad_rejonowy_zyrardowie', v_parent_id, 'Sąd Rejonowy w Żyrardowie', 'Żyrardów');

    -- sad_okregowy_poznan (21 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_poznan';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_chodziezy', v_parent_id, 'Sąd Rejonowy w Chodzieży', 'Chodzież'),
        ('regional', 'sad_rejonowy_gnieznie', v_parent_id, 'Sąd Rejonowy w Gnieźnie', 'Gniezno'),
        ('regional', 'sad_rejonowy_gostyniu', v_parent_id, 'Sąd Rejonowy w Gostyniu', 'Gostyń'),
        ('regional', 'sad_rejonowy_grodzisku_wielkopolskim', v_parent_id, 'Sąd Rejonowy w Grodzisku Wielkopolskim', 'Grodzisk Wielkopolski'),
        ('regional', 'sad_rejonowy_koscianie', v_parent_id, 'Sąd Rejonowy w Kościanie', 'Kościan'),
        ('regional', 'sad_rejonowy_lesznie', v_parent_id, 'Sąd Rejonowy w Lesznie', 'Leszno'),
        ('regional', 'sad_rejonowy_nowym_tomyslu', v_parent_id, 'Sąd Rejonowy w Nowym Tomyślu', 'Nowy Tomyśl'),
        ('regional', 'sad_rejonowy_obornikach', v_parent_id, 'Sąd Rejonowy w Obornikach', 'Oborniki'),
        ('regional', 'sad_rejonowy_pile', v_parent_id, 'Sąd Rejonowy w Pile', 'Piła'),
        ('regional', 'sad_rejonowy_poznan_grunwald_i_jezyce', v_parent_id, 'Sąd Rejonowy Poznań-Grunwald i Jeżyce w Poznaniu', 'Poznań'),
        ('regional', 'sad_rejonowy_poznan_nowe_miasto_i_wilda', v_parent_id, 'Sąd Rejonowy Poznań-Nowe Miasto i Wilda w Poznaniu', 'Poznań'),
        ('regional', 'sad_rejonowy_poznan_stare_miasto', v_parent_id, 'Sąd Rejonowy Poznań-Stare Miasto w Poznaniu', 'Poznań'),
        ('regional', 'sad_rejonowy_rawiczu', v_parent_id, 'Sąd Rejonowy w Rawiczu', 'Rawicz'),
        ('regional', 'sad_rejonowy_sremie', v_parent_id, 'Sąd Rejonowy w Śremie', 'Śrem'),
        ('regional', 'sad_rejonowy_srodzie_wielkopolskiej', v_parent_id, 'Sąd Rejonowy w Środzie Wielkopolskiej', 'Środa Wielkopolska'),
        ('regional', 'sad_rejonowy_szamotulach', v_parent_id, 'Sąd Rejonowy w Szamotułach', 'Szamotuły'),
        ('regional', 'sad_rejonowy_trzciance', v_parent_id, 'Sąd Rejonowy w Trzciance', 'Trzcianka'),
        ('regional', 'sad_rejonowy_wagrowcu', v_parent_id, 'Sąd Rejonowy w Wągrowcu', 'Wągrowiec'),
        ('regional', 'sad_rejonowy_wolsztynie', v_parent_id, 'Sąd Rejonowy w Wolsztynie', 'Wolsztyn'),
        ('regional', 'sad_rejonowy_wrzesni', v_parent_id, 'Sąd Rejonowy we Wrześni', 'Września'),
        ('regional', 'sad_rejonowy_zlotowie', v_parent_id, 'Sąd Rejonowy w Złotowie', 'Złotów');

    -- sad_okregowy_przemysl (4 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_przemysl';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_jaroslawiu', v_parent_id, 'Sąd Rejonowy w Jarosławiu', 'Jarosław'),
        ('regional', 'sad_rejonowy_lubaczowie', v_parent_id, 'Sąd Rejonowy w Lubaczowie', 'Lubaczów'),
        ('regional', 'sad_rejonowy_przemyslu', v_parent_id, 'Sąd Rejonowy w Przemyślu', 'Przemyśl'),
        ('regional', 'sad_rejonowy_przeworsku', v_parent_id, 'Sąd Rejonowy w Przeworsku', 'Przeworsk');

    -- sad_okregowy_radom (7 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_radom';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_grojcu', v_parent_id, 'Sąd Rejonowy w Grójcu', 'Grójec'),
        ('regional', 'sad_rejonowy_kozienicach', v_parent_id, 'Sąd Rejonowy w Kozienicach', 'Kozienice'),
        ('regional', 'sad_rejonowy_lipsku', v_parent_id, 'Sąd Rejonowy w Lipsku', 'Lipsk'),
        ('regional', 'sad_rejonowy_przysusze', v_parent_id, 'Sąd Rejonowy w Przysusze', 'Przysucha'),
        ('regional', 'sad_rejonowy_radomiu', v_parent_id, 'Sąd Rejonowy w Radomiu', 'Radom'),
        ('regional', 'sad_rejonowy_szydlowcu', v_parent_id, 'Sąd Rejonowy w Szydłowcu', 'Szydłowiec'),
        ('regional', 'sad_rejonowy_zwoleniu', v_parent_id, 'Sąd Rejonowy w Zwoleniu', 'Zwoleń');

    -- sad_okregowy_rybnik (5 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_rybnik';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_jastrzebiu_zdroju', v_parent_id, 'Sąd Rejonowy w Jastrzębiu-Zdroju', 'Jastrzębie-Zdrój'),
        ('regional', 'sad_rejonowy_raciborzu', v_parent_id, 'Sąd Rejonowy w Raciborzu', 'Racibórz'),
        ('regional', 'sad_rejonowy_rybniku', v_parent_id, 'Sąd Rejonowy w Rybniku', 'Rybnik'),
        ('regional', 'sad_rejonowy_wodzislawiu_slaskim', v_parent_id, 'Sąd Rejonowy w Wodzisławiu Śląskim', 'Wodzisław Śląski'),
        ('regional', 'sad_rejonowy_zorach', v_parent_id, 'Sąd Rejonowy w Żorach', 'Żory');

    -- sad_okregowy_rzeszow (6 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_rzeszow';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_debicy', v_parent_id, 'Sąd Rejonowy w Dębicy', 'Dębica'),
        ('regional', 'sad_rejonowy_lancucie', v_parent_id, 'Sąd Rejonowy w Łańcucie', 'Łańcut'),
        ('regional', 'sad_rejonowy_lezajsku', v_parent_id, 'Sąd Rejonowy w Leżajsku', 'Leżajsk'),
        ('regional', 'sad_rejonowy_ropczycach', v_parent_id, 'Sąd Rejonowy w Ropczycach', 'Ropczyce'),
        ('regional', 'sad_rejonowy_rzeszowie', v_parent_id, 'Sąd Rejonowy w Rzeszowie', 'Rzeszów'),
        ('regional', 'sad_rejonowy_strzyzowie', v_parent_id, 'Sąd Rejonowy w Strzyżowie', 'Strzyżów');

    -- sad_okregowy_siedlce (5 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_siedlce';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_garwolinie', v_parent_id, 'Sąd Rejonowy w Garwolinie', 'Garwolin'),
        ('regional', 'sad_rejonowy_minsku_mazowieckim', v_parent_id, 'Sąd Rejonowy w Mińsku Mazowieckim', 'Mińsk Mazowiecki'),
        ('regional', 'sad_rejonowy_siedlcach', v_parent_id, 'Sąd Rejonowy w Siedlcach', 'Siedlce'),
        ('regional', 'sad_rejonowy_sokolowie_podlaskim', v_parent_id, 'Sąd Rejonowy w Sokołowie Podlaskim', 'Sokołów Podlaski'),
        ('regional', 'sad_rejonowy_wegrowie', v_parent_id, 'Sąd Rejonowy w Węgrowie', 'Węgrów');

    -- sad_okregowy_sieradz (4 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_sieradz';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_lasku', v_parent_id, 'Sąd Rejonowy w Łasku', 'Łask'),
        ('regional', 'sad_rejonowy_sieradzu', v_parent_id, 'Sąd Rejonowy w Sieradzu', 'Sieradz'),
        ('regional', 'sad_rejonowy_wieluniu', v_parent_id, 'Sąd Rejonowy w Wieluniu', 'Wieluń'),
        ('regional', 'sad_rejonowy_zdunskiej_woli', v_parent_id, 'Sąd Rejonowy w Zduńskiej Woli', 'Zduńska Wola');

    -- sad_okregowy_slupsk (6 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_slupsk';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_bytowie', v_parent_id, 'Sąd Rejonowy w Bytowie', 'Bytów'),
        ('regional', 'sad_rejonowy_chojnicach', v_parent_id, 'Sąd Rejonowy w Chojnicach', 'Chojnice'),
        ('regional', 'sad_rejonowy_czluchowie', v_parent_id, 'Sąd Rejonowy w Człuchowie', 'Człuchów'),
        ('regional', 'sad_rejonowy_leborku', v_parent_id, 'Sąd Rejonowy w Lęborku', 'Lębork'),
        ('regional', 'sad_rejonowy_miastku', v_parent_id, 'Sąd Rejonowy w Miastku', 'Miastko'),
        ('regional', 'sad_rejonowy_slupsku', v_parent_id, 'Sąd Rejonowy w Słupsku', 'Słupsk');

    -- sad_okregowy_sosnowiec (6 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_sosnowiec';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_bedzinie', v_parent_id, 'Sąd Rejonowy w Będzinie', 'Będzin'),
        ('regional', 'sad_rejonowy_czeladz', v_parent_id, 'Sąd Rejonowy w Czeladzi', 'Czeladź'),
        ('regional', 'sad_rejonowy_dabrowie_gorniczej', v_parent_id, 'Sąd Rejonowy w Dąbrowie Górniczej', 'Dąbrowa Górnicza'),
        ('regional', 'sad_rejonowy_jaworznie', v_parent_id, 'Sąd Rejonowy w Jaworznie', 'Jaworzno'),
        ('regional', 'sad_rejonowy_sosnowcu', v_parent_id, 'Sąd Rejonowy w Sosnowcu', 'Sosnowiec'),
        ('regional', 'sad_rejonowy_zawierciu', v_parent_id, 'Sąd Rejonowy w Zawierciu', 'Zawiercie');

    -- sad_okregowy_suwalki (4 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_suwalki';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_augustowie', v_parent_id, 'Sąd Rejonowy w Augustowie', 'Augustów'),
        ('regional', 'sad_rejonowy_elku', v_parent_id, 'Sąd Rejonowy w Ełku', 'Ełk'),
        ('regional', 'sad_rejonowy_olecku', v_parent_id, 'Sąd Rejonowy w Olecku', 'Olecko'),
        ('regional', 'sad_rejonowy_suwalkach', v_parent_id, 'Sąd Rejonowy w Suwałkach', 'Suwałki');

    -- sad_okregowy_swidnica (5 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_swidnica';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_dzierzoniowie', v_parent_id, 'Sąd Rejonowy w Dzierżoniowie', 'Dzierżoniów'),
        ('regional', 'sad_rejonowy_klodzku', v_parent_id, 'Sąd Rejonowy w Kłodzku', 'Kłodzko'),
        ('regional', 'sad_rejonowy_swidnicy', v_parent_id, 'Sąd Rejonowy w Świdnicy', 'Świdnica'),
        ('regional', 'sad_rejonowy_walbrzychu', v_parent_id, 'Sąd Rejonowy w Wałbrzychu', 'Wałbrzych'),
        ('regional', 'sad_rejonowy_zabkowicach_slaskich', v_parent_id, 'Sąd Rejonowy w Ząbkowicach Śląskich', 'Ząbkowice Śląskie');

    -- sad_okregowy_szczecin (11 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_szczecin';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_choszcznie', v_parent_id, 'Sąd Rejonowy w Choszcznie', 'Choszczno'),
        ('regional', 'sad_rejonowy_goleniowie', v_parent_id, 'Sąd Rejonowy w Goleniowie', 'Goleniów'),
        ('regional', 'sad_rejonowy_gryficach', v_parent_id, 'Sąd Rejonowy w Gryficach', 'Gryfice'),
        ('regional', 'sad_rejonowy_gryfinie', v_parent_id, 'Sąd Rejonowy w Gryfinie', 'Gryfino'),
        ('regional', 'sad_rejonowy_kamieniu_pomorskim', v_parent_id, 'Sąd Rejonowy w Kamieniu Pomorskim', 'Kamień Pomorski'),
        ('regional', 'sad_rejonowy_lobzie', v_parent_id, 'Sąd Rejonowy w Łobzie', 'Łobez'),
        ('regional', 'sad_rejonowy_mysliborzu', v_parent_id, 'Sąd Rejonowy w Myśliborzu', 'Myślibórz'),
        ('regional', 'sad_rejonowy_stargardzie', v_parent_id, 'Sąd Rejonowy w Stargardzie', 'Stargard'),
        ('regional', 'sad_rejonowy_swinoujsciu', v_parent_id, 'Sąd Rejonowy w Świnoujściu', 'Świnoujście'),
        ('regional', 'sad_rejonowy_szczecin_centrum', v_parent_id, 'Sąd Rejonowy Szczecin-Centrum w Szczecinie', 'Szczecin'),
        ('regional', 'sad_rejonowy_szczecin_prawobrzeze_i_zachod', v_parent_id, 'Sąd Rejonowy Szczecin-Prawobrzeże i Zachód w Szczecinie', 'Szczecin');

    -- sad_okregowy_tarnobrzeg (5 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_tarnobrzeg';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_kolbuszowej', v_parent_id, 'Sąd Rejonowy w Kolbuszowej', 'Kolbuszowa'),
        ('regional', 'sad_rejonowy_mielcu', v_parent_id, 'Sąd Rejonowy w Mielcu', 'Mielec'),
        ('regional', 'sad_rejonowy_nisku', v_parent_id, 'Sąd Rejonowy w Nisku', 'Nisk'),
        ('regional', 'sad_rejonowy_stalowej_woli', v_parent_id, 'Sąd Rejonowy w Stalowej Woli', 'Stalowa Wola'),
        ('regional', 'sad_rejonowy_tarnobrzegu', v_parent_id, 'Sąd Rejonowy w Tarnobrzegu', 'Tarnobrzeg');

    -- sad_okregowy_tarnow (4 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_tarnow';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_bochni', v_parent_id, 'Sąd Rejonowy w Bochni', 'Bochnia'),
        ('regional', 'sad_rejonowy_brzesku', v_parent_id, 'Sąd Rejonowy w Brzesku', 'Brzesk'),
        ('regional', 'sad_rejonowy_dabrowie_tarnowskiej', v_parent_id, 'Sąd Rejonowy w Dąbrowie Tarnowskiej', 'Dąbrowa Tarnowska'),
        ('regional', 'sad_rejonowy_tarnowie', v_parent_id, 'Sąd Rejonowy w Tarnowie', 'Tarnów');

    -- sad_okregowy_torun (6 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_torun';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_brodnicy', v_parent_id, 'Sąd Rejonowy w Brodnicy', 'Brodnica'),
        ('regional', 'sad_rejonowy_chelmnie', v_parent_id, 'Sąd Rejonowy w Chełmnie', 'Chełmno'),
        ('regional', 'sad_rejonowy_golubiu_dobrzyniu', v_parent_id, 'Sąd Rejonowy w Golubiu-Dobrzyniu', 'Golubiu-Dobrzyń'),
        ('regional', 'sad_rejonowy_grudziadzu', v_parent_id, 'Sąd Rejonowy w Grudziądzu', 'Grudziądz'),
        ('regional', 'sad_rejonowy_toruniu', v_parent_id, 'Sąd Rejonowy w Toruniu', 'Toruń'),
        ('regional', 'sad_rejonowy_wabrzeznie', v_parent_id, 'Sąd Rejonowy w Wąbrzeźnie', 'Wąbrzeźno');

    -- sad_okregowy_warszawa (8 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_warszawa';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_grodzisku_mazowieckim', v_parent_id, 'Sąd Rejonowy w Grodzisku Mazowieckim', 'Grodzisk Mazowiecki'),
        ('regional', 'sad_rejonowy_piasecznie', v_parent_id, 'Sąd Rejonowy w Piasecznie', 'Piaseczno'),
        ('regional', 'sad_rejonowy_pruszkowie', v_parent_id, 'Sąd Rejonowy w Pruszkowie', 'Pruszków'),
        ('regional', 'sad_rejonowy_warszawa_miasto_stoleczne', v_parent_id, 'Sąd Rejonowy dla miasta stołecznego Warszawy w Warszawie', 'Warszawa'),
        ('regional', 'sad_rejonowy_warszawy_mokotowa', v_parent_id, 'Sąd Rejonowy dla Warszawy-Mokotowa w Warszawie', 'Warszawa'),
        ('regional', 'sad_rejonowy_warszawy_srodmiescia', v_parent_id, 'Sąd Rejonowy dla Warszawy-Śródmieścia w Warszawie', 'Warszawa'),
        ('regional', 'sad_rejonowy_warszawy_woli', v_parent_id, 'Sąd Rejonowy dla Warszawy-Woli w Warszawie', 'Warszawa'),
        ('regional', 'sad_rejonowy_warszawy_zoliborza', v_parent_id, 'Sąd Rejonowy dla Warszawy-Żoliborza w Warszawie', 'Warszawa');

    -- sad_okregowy_warszawa_praga (6 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_warszawa_praga';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_legionowie', v_parent_id, 'Sąd Rejonowy w Legionowie', 'Legionów'),
        ('regional', 'sad_rejonowy_nowym_dworze_mazowieckim', v_parent_id, 'Sąd Rejonowy w Nowym Dworze Mazowieckim', 'Nowy Dwór Mazowiecki'),
        ('regional', 'sad_rejonowy_otwocku', v_parent_id, 'Sąd Rejonowy w Otwocku', 'Otwock'),
        ('regional', 'sad_rejonowy_warszawy_pragi_polnoc', v_parent_id, 'Sąd Rejonowy dla Warszawy Pragi-Północ w Warszawie', 'Warszawa'),
        ('regional', 'sad_rejonowy_warszawy_pragi_poludnie', v_parent_id, 'Sąd Rejonowy dla Warszawy Pragi-Południe w Warszawie', 'Warszawa'),
        ('regional', 'sad_rejonowy_wolominie', v_parent_id, 'Sąd Rejonowy w Wołominie', 'Wołomin');

    -- sad_okregowy_wloclawek (5 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_wloclawek';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_aleksandrowie_kujawskim', v_parent_id, 'Sąd Rejonowy w Aleksandrowie Kujawskim', 'Aleksandrów Kujawski'),
        ('regional', 'sad_rejonowy_lipnie', v_parent_id, 'Sąd Rejonowy w Lipnie', 'Lipno'),
        ('regional', 'sad_rejonowy_radziejowie', v_parent_id, 'Sąd Rejonowy w Radziejowie', 'Radziejów'),
        ('regional', 'sad_rejonowy_rypinie', v_parent_id, 'Sąd Rejonowy w Rypinie', 'Rypin'),
        ('regional', 'sad_rejonowy_wloclawku', v_parent_id, 'Sąd Rejonowy we Włocławku', 'Włocławek');

    -- sad_okregowy_wroclaw (10 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_wroclaw';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_miliczu', v_parent_id, 'Sąd Rejonowy w Miliczu', 'Milicz'),
        ('regional', 'sad_rejonowy_olawie', v_parent_id, 'Sąd Rejonowy w Oławie', 'Oława'),
        ('regional', 'sad_rejonowy_olesnicy', v_parent_id, 'Sąd Rejonowy w Oleśnicy', 'Oleśnica'),
        ('regional', 'sad_rejonowy_srodzie_slaskiej', v_parent_id, 'Sąd Rejonowy w Środzie Śląskiej', 'Środa Śląska'),
        ('regional', 'sad_rejonowy_strzelinie', v_parent_id, 'Sąd Rejonowy w Strzelinie', 'Strzelin'),
        ('regional', 'sad_rejonowy_trzebnicy', v_parent_id, 'Sąd Rejonowy w Trzebnicy', 'Trzebnica'),
        ('regional', 'sad_rejonowy_wolowie', v_parent_id, 'Sąd Rejonowy w Wołowie', 'Wołów'),
        ('regional', 'sad_rejonowy_wroclawia_fabrycznej', v_parent_id, 'Sąd Rejonowy dla Wrocławia-Fabrycznej we Wrocławiu', 'Wrocław'),
        ('regional', 'sad_rejonowy_wroclawia_krzykow', v_parent_id, 'Sąd Rejonowy dla Wrocławia-Krzyków we Wrocławiu', 'Wrocław'),
        ('regional', 'sad_rejonowy_wroclawia_srodmiescia', v_parent_id, 'Sąd Rejonowy dla Wrocławia-Śródmieścia we Wrocławiu', 'Wrocław');

    -- sad_okregowy_zamosc (6 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_zamosc';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_bilgoraju', v_parent_id, 'Sąd Rejonowy w Biłgoraju', 'Biłgoraj'),
        ('regional', 'sad_rejonowy_hrubieszowie', v_parent_id, 'Sąd Rejonowy w Hrubieszowie', 'Hrubieszów'),
        ('regional', 'sad_rejonowy_janowie_lubelskim', v_parent_id, 'Sąd Rejonowy w Janowie Lubelskim', 'Janów Lubelski'),
        ('regional', 'sad_rejonowy_krasnymstawie', v_parent_id, 'Sąd Rejonowy w Krasnymstawie', 'Krasnystaw'),
        ('regional', 'sad_rejonowy_tomaszowie_lubelskim', v_parent_id, 'Sąd Rejonowy w Tomaszowie Lubelskim', 'Tomaszów Lubelski'),
        ('regional', 'sad_rejonowy_zamosciu', v_parent_id, 'Sąd Rejonowy w Zamościu', 'Zamość');

    -- sad_okregowy_zielona_gora (7 courts)
    SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_zielona_gora';
    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city) VALUES
        ('regional', 'sad_rejonowy_krosnie_odrzanskim', v_parent_id, 'Sąd Rejonowy w Krośnie Odrzańskim', 'Krosno Odrzańskie'),
        ('regional', 'sad_rejonowy_nowej_soli', v_parent_id, 'Sąd Rejonowy w Nowej Soli', 'Nowa Sól'),
        ('regional', 'sad_rejonowy_swiebodzinie', v_parent_id, 'Sąd Rejonowy w Świebodzinie', 'Świebodzin'),
        ('regional', 'sad_rejonowy_wschowie', v_parent_id, 'Sąd Rejonowy we Wschowie', 'Wschów'),
        ('regional', 'sad_rejonowy_zaganiu', v_parent_id, 'Sąd Rejonowy w Żaganiu', 'Żagań'),
        ('regional', 'sad_rejonowy_zarach', v_parent_id, 'Sąd Rejonowy w Żarach', 'Żary'),
        ('regional', 'sad_rejonowy_zielonej_gorze', v_parent_id, 'Sąd Rejonowy w Zielonej Górze', 'Zielona Góra');

END $$;

COMMIT;