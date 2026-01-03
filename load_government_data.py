#!/usr/bin/env python3
"""
TPHSRS Data Loader - โหลดข้อมูลโรงพยาบาลจากแหล่งข้อมูลภาครัฐไทย
สำหรับโครงงาน Thai Public Health Service Recommendation System
"""

import pandas as pd
import json
import requests
from datetime import datetime

SAMPLE_THAI_HOSPITALS_DATA = """
hospital_code,hospital_name_th,hospital_name_en,hospital_type,province,region,phone,emergency_phone,address,website,beds,latitude,longitude,accepts_universal_coverage,accepts_social_security,accepts_civil_servant
10682,โรงพยาบาลศิริราช,Siriraj Hospital,PublicHospital,Bangkok,Central,02-419-1000,02-419-7000,2 Wanglang Road Bangkok Noi Bangkok 10700,https://www.siphhospital.com,2300,13.7563,100.4850,1,1,1
10684,โรงพยาบาลรามาธิบดี,Ramathibodi Hospital,PublicHospital,Bangkok,Central,02-201-1000,02-201-1500,270 Rama VI Road Ratchathewi Bangkok 10400,https://www.ramathibodi.mahidol.ac.th,1400,13.7594,100.5256,1,1,1
10685,โรงพยาบาลจุฬาลงกรณ์,Chulalongkorn Hospital,PublicHospital,Bangkok,Central,02-256-4000,02-256-4321,1873 Rama IV Road Pathumwan Bangkok 10330,https://www.chulahosp.org,1500,13.7307,100.5418,1,1,1
13743,โรงพยาบาลมหาราชนครเชียงใหม่,Maharaj Nakorn Chiang Mai Hospital,PublicHospital,Chiang Mai,Northern,053-936-000,053-936-500,110 Inthawarorot Road Sriphum Muang Chiang Mai 50200,https://www.maharajnakorn.go.th,1200,18.7883,98.9853,1,1,1
94226,โรงพยาบาลสงขลานครินทร์,Songklanagarind Hospital,PublicHospital,Songkhla,Southern,074-451-000,074-451-555,15 Kanjanavanich Road Hat Yai Songkhla 90110,https://www.hospital.psu.ac.th,800,7.0088,100.4969,1,1,1
10682,โรงพยาบาลขอนแก่น,Khon Kaen Hospital,PublicHospital,Khon Kaen,Northeastern,043-348-000,043-348-888,123 Mittraphap Road Muang Khon Kaen 40002,https://www.kkh.go.th,1000,16.4322,102.8236,1,1,1
11060,โรงพยาบาลบำรุงราษฎร์,Bumrungrad Hospital,PrivateHospital,Bangkok,Central,02-066-8888,02-011-3388,33 Sukhumvit 3 Watthana Bangkok 10110,https://www.bumrungrad.com,580,13.7443,100.5580,0,1,0
10936,โรงพยาบาลกรุงเทพ,Bangkok Hospital,PrivateHospital,Bangkok,Central,02-310-3000,1719,2 Soi Soonvijai 7 New Petchburi Road Bangkok 10310,https://www.bangkokhospital.com,550,13.7521,100.5692,0,1,0
51289,โรงพยาบาลเชียงใหม่ราม,Chiang Mai Ram Hospital,PrivateHospital,Chiang Mai,Northern,053-920-300,053-920-444,8 Boonruangrit Road Muang Chiang Mai 50200,https://www.chiangmairam.com,420,18.7877,98.9900,0,1,0
10820,โรงพยาบาลสมิติเวช,Samitivej Hospital,PrivateHospital,Bangkok,Central,02-022-2222,02-022-3000,133 Sukhumvit 49 Watthana Bangkok 10110,https://www.samitivejhospitals.com,500,13.7365,100.5838,0,1,0
"""

DEPARTMENTS_DATA = {
    "InternalMedicine": {"name_th": "แผนกอายุรกรรม", "name_en": "Internal Medicine"},
    "Surgery": {"name_th": "แผนกศัลยกรรม", "name_en": "Surgery"},
    "Pediatrics": {"name_th": "แผนกกุมารเวชกรรม", "name_en": "Pediatrics"},
    "ObstetricsGynecology": {"name_th": "แผนกสูติ-นรีเวช", "name_en": "Obstetrics and Gynecology"},
    "Orthopedics": {"name_th": "แผนกศัลยกรรมกระดูก", "name_en": "Orthopedics"},
    "Cardiology": {"name_th": "แผนกโรคหัวใจ", "name_en": "Cardiology"},
    "Neurology": {"name_th": "แผนกโรคระบบประสาท", "name_en": "Neurology"},
    "Dermatology": {"name_th": "แผนกโรคผิวหนัง", "name_en": "Dermatology"},
    "Ophthalmology": {"name_th": "แผนกจักษุ", "name_en": "Ophthalmology"},
    "ENT": {"name_th": "แผนกหู คอ จมูก", "name_en": "ENT (Ear Nose Throat)"},
    "Emergency": {"name_th": "แผนกฉุกเฉิน", "name_en": "Emergency Department"},
    "Oncology": {"name_th": "แผนกมะเร็งวิทยา", "name_en": "Oncology"},
    "DentalDepartment": {"name_th": "แผนกทันตกรรม", "name_en": "Dental Department"},
    "Psychiatry": {"name_th": "แผนกจิตเวช", "name_en": "Psychiatry"}
}

SYMPTOMS_DATA = {
    "Fever": {"name_th": "ไข้", "name_en": "Fever", "department": "InternalMedicine", "severity": "Medium", "description": "มีไข้สูง อุณหภูมิร่างกายเกิน 38 องศาเซลเซียส"},
    "Cough": {"name_th": "ไอ", "name_en": "Cough", "department": "InternalMedicine", "severity": "Low", "description": "ไอเรื้อรัง ไอมีเสมหะ หรือไอแห้ง"},
    "SkinRash": {"name_th": "ผื่นคัน", "name_en": "Skin Rash", "department": "Dermatology", "severity": "Low", "description": "ผื่นคันที่ผิวหนัง มีตุ่มหรือผิวหนังแดง"},
    "Toothache": {"name_th": "ปวดฟัน", "name_en": "Toothache", "department": "DentalDepartment", "severity": "Medium", "description": "ปวดฟัน เหงือกบวม มีอาการอักเสบบริเวณช่องปาก"},
    "ChestPain": {"name_th": "เจ็บหน้าอก", "name_en": "Chest Pain", "department": "Cardiology", "severity": "High", "description": "เจ็บหน้าอก หายใจลำบาก อาจมีอาการแน่นหน้าอก"},
    "Headache": {"name_th": "ปวดหัว", "name_en": "Headache", "department": "Neurology", "severity": "Medium", "description": "ปวดศีรษะรุนแรง ปวดเมื่อยบริเวณศีรษะ"},
    "Stomachache": {"name_th": "ปวดท้อง", "name_en": "Stomachache", "department": "InternalMedicine", "severity": "Medium", "description": "ปวดท้อง ท้องเสีย ท้องผูก"},
    "BoneFracture": {"name_th": "กระดูกหัก", "name_en": "Bone Fracture", "department": "Orthopedics", "severity": "High", "description": "กระดูกหัก บาดเจ็บที่กระดูก"},
    "EyePain": {"name_th": "ตาเจ็บ", "name_en": "Eye Pain", "department": "Ophthalmology", "severity": "Medium", "description": "ตาแดง ตาเจ็บ มองเห็นไม่ชัด"},
    "SoreThroat": {"name_th": "เจ็บคอ", "name_en": "Sore Throat", "department": "ENT", "severity": "Low", "description": "เจ็บคอ คออักเสบ กลืนลำบาก"},
    "Dizziness": {"name_th": "เวียนศีรษะ", "name_en": "Dizziness", "department": "Neurology", "severity": "Medium", "description": "วิงเวียนศีรษะ เดินเซ เสียการทรงตัว"},
    "BackPain": {"name_th": "ปวดหลัง", "name_en": "Back Pain", "department": "Orthopedics", "severity": "Medium", "description": "ปวดหลัง ปวดเอว ปวดกระดูกสันหลัง"},
    "Vomiting": {"name_th": "อาเจียน", "name_en": "Vomiting", "department": "InternalMedicine", "severity": "Medium", "description": "อาเจียน คลื่นไส้ อาการไม่สบายกระเพาะ"},
    "Depression": {"name_th": "ซึมเศร้า", "name_en": "Depression", "department": "Psychiatry", "severity": "High", "description": "อาการซึมเศร้า เบื่อหน่าย ไม่มีแรงใจ"},
    "Diarrhea": {"name_th": "ท้องเสีย", "name_en": "Diarrhea", "department": "InternalMedicine", "severity": "Low", "description": "ท้องเสีย ถ่ายเหลว ปวดท้อง"}
}

def generate_ttl_ontology(df_hospitals):
    """สร้าง TTL Ontology จากข้อมูลโรงพยาบาล"""
    
    ttl_content = """<?xml version="1.0"?>
<rdf:RDF xmlns="http://www.semanticweb.org/204424/TPHSRS/"
     xml:base="http://www.semanticweb.org/204424/TPHSRS/"
     xmlns:owl="http://www.w3.org/2002/07/owl#"
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:xml="http://www.w3.org/XML/1998/namespace"
     xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
     xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
    
    <owl:Ontology rdf:about="http://www.semanticweb.org/204424/TPHSRS">
        <rdfs:comment>Thai Public Health Service Recommendation System - Generated from Government Open Data</rdfs:comment>
        <rdfs:comment>Data Source: Simulated from data.go.th structure</rdfs:comment>
        <rdfs:comment>Generated on: {date}</rdfs:comment>
    </owl:Ontology>

""".format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    ttl_content += """
    <owl:ObjectProperty rdf:about="http://www.semanticweb.org/204424/TPHSRS/acceptsRight">
        <rdfs:domain rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Hospital"/>
        <rdfs:range rdf:resource="http://www.semanticweb.org/204424/TPHSRS/MedicalRight"/>
        <rdfs:label xml:lang="th">รับสิทธิการรักษา</rdfs:label>
    </owl:ObjectProperty>

    <owl:ObjectProperty rdf:about="http://www.semanticweb.org/204424/TPHSRS/suggestsDepartment">
        <rdfs:domain rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Symptom"/>
        <rdfs:range rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Department"/>
        <rdfs:label xml:lang="th">แนะนำแผนกการรักษา</rdfs:label>
    </owl:ObjectProperty>

    <owl:ObjectProperty rdf:about="http://www.semanticweb.org/204424/TPHSRS/hasDepartment">
        <rdfs:domain rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Hospital"/>
        <rdfs:range rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Department"/>
        <rdfs:label xml:lang="th">มีแผนก</rdfs:label>
    </owl:ObjectProperty>

    <owl:DatatypeProperty rdf:about="http://www.semanticweb.org/204424/TPHSRS/hasPhoneNumber">
        <rdfs:domain rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Hospital"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#string"/>
    </owl:DatatypeProperty>

    <owl:DatatypeProperty rdf:about="http://www.semanticweb.org/204424/TPHSRS/hasEmergencyNumber">
        <rdfs:domain rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Hospital"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#string"/>
    </owl:DatatypeProperty>

    <owl:DatatypeProperty rdf:about="http://www.semanticweb.org/204424/TPHSRS/locationProvince">
        <rdfs:domain rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Hospital"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#string"/>
    </owl:DatatypeProperty>

    <owl:DatatypeProperty rdf:about="http://www.semanticweb.org/204424/TPHSRS/locationRegion">
        <rdfs:domain rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Hospital"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#string"/>
    </owl:DatatypeProperty>

    <owl:DatatypeProperty rdf:about="http://www.semanticweb.org/204424/TPHSRS/hasAddress">
        <rdfs:domain rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Hospital"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#string"/>
    </owl:DatatypeProperty>

    <owl:DatatypeProperty rdf:about="http://www.semanticweb.org/204424/TPHSRS/hasWebsite">
        <rdfs:domain rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Hospital"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#string"/>
    </owl:DatatypeProperty>

    <owl:DatatypeProperty rdf:about="http://www.semanticweb.org/204424/TPHSRS/numberOfBeds">
        <rdfs:domain rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Hospital"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#integer"/>
    </owl:DatatypeProperty>

    <owl:DatatypeProperty rdf:about="http://www.semanticweb.org/204424/TPHSRS/latitude">
        <rdfs:domain rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Hospital"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#float"/>
    </owl:DatatypeProperty>

    <owl:DatatypeProperty rdf:about="http://www.semanticweb.org/204424/TPHSRS/longitude">
        <rdfs:domain rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Hospital"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#float"/>
    </owl:DatatypeProperty>

    <owl:DatatypeProperty rdf:about="http://www.semanticweb.org/204424/TPHSRS/hospitalCode">
        <rdfs:domain rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Hospital"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#string"/>
        <rdfs:label>H-Code</rdfs:label>
    </owl:DatatypeProperty>

    <owl:DatatypeProperty rdf:about="http://www.semanticweb.org/204424/TPHSRS/hasDescription">
        <rdfs:domain rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Symptom"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#string"/>
    </owl:DatatypeProperty>

    <owl:DatatypeProperty rdf:about="http://www.semanticweb.org/204424/TPHSRS/severityLevel">
        <rdfs:domain rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Symptom"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#string"/>
    </owl:DatatypeProperty>

    <owl:Class rdf:about="http://www.semanticweb.org/204424/TPHSRS/Hospital">
        <rdfs:label xml:lang="th">สถานพยาบาล</rdfs:label>
        <rdfs:label xml:lang="en">Hospital</rdfs:label>
    </owl:Class>

    <owl:Class rdf:about="http://www.semanticweb.org/204424/TPHSRS/PublicHospital">
        <rdfs:subClassOf rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Hospital"/>
        <rdfs:label xml:lang="th">โรงพยาบาลรัฐ</rdfs:label>
    </owl:Class>

    <owl:Class rdf:about="http://www.semanticweb.org/204424/TPHSRS/PrivateHospital">
        <rdfs:subClassOf rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Hospital"/>
        <rdfs:label xml:lang="th">โรงพยาบาลเอกชน</rdfs:label>
    </owl:Class>

    <owl:Class rdf:about="http://www.semanticweb.org/204424/TPHSRS/MedicalRight">
        <rdfs:label xml:lang="th">สิทธิการรักษา</rdfs:label>
    </owl:Class>

    <owl:Class rdf:about="http://www.semanticweb.org/204424/TPHSRS/GoldCardRight">
        <rdfs:subClassOf rdf:resource="http://www.semanticweb.org/204424/TPHSRS/MedicalRight"/>
        <rdfs:label xml:lang="th">สิทธิบัตรทอง</rdfs:label>
    </owl:Class>

    <owl:Class rdf:about="http://www.semanticweb.org/204424/TPHSRS/SocialSecurityRight">
        <rdfs:subClassOf rdf:resource="http://www.semanticweb.org/204424/TPHSRS/MedicalRight"/>
        <rdfs:label xml:lang="th">สิทธิประกันสังคม</rdfs:label>
    </owl:Class>

    <owl:Class rdf:about="http://www.semanticweb.org/204424/TPHSRS/CivilServantRight">
        <rdfs:subClassOf rdf:resource="http://www.semanticweb.org/204424/TPHSRS/MedicalRight"/>
        <rdfs:label xml:lang="th">สิทธิข้าราชการ</rdfs:label>
    </owl:Class>

    <owl:Class rdf:about="http://www.semanticweb.org/204424/TPHSRS/Symptom">
        <rdfs:label xml:lang="th">อาการป่วย</rdfs:label>
    </owl:Class>

    <owl:Class rdf:about="http://www.semanticweb.org/204424/TPHSRS/Department">
        <rdfs:label xml:lang="th">แผนก</rdfs:label>
    </owl:Class>

    <owl:NamedIndividual rdf:about="http://www.semanticweb.org/204424/TPHSRS/GoldCard">
        <rdf:type rdf:resource="http://www.semanticweb.org/204424/TPHSRS/GoldCardRight"/>
        <rdfs:label xml:lang="th">บัตรทอง</rdfs:label>
    </owl:NamedIndividual>

    <owl:NamedIndividual rdf:about="http://www.semanticweb.org/204424/TPHSRS/SocialSecurity">
        <rdf:type rdf:resource="http://www.semanticweb.org/204424/TPHSRS/SocialSecurityRight"/>
        <rdfs:label xml:lang="th">ประกันสังคม</rdfs:label>
    </owl:NamedIndividual>

    <owl:NamedIndividual rdf:about="http://www.semanticweb.org/204424/TPHSRS/CivilServant">
        <rdf:type rdf:resource="http://www.semanticweb.org/204424/TPHSRS/CivilServantRight"/>
        <rdfs:label xml:lang="th">ข้าราชการ</rdfs:label>
    </owl:NamedIndividual>

"""

    for dept_id, dept_info in DEPARTMENTS_DATA.items():
        ttl_content += f"""    <owl:NamedIndividual rdf:about="http://www.semanticweb.org/204424/TPHSRS/{dept_id}">
        <rdf:type rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Department"/>
        <rdfs:label xml:lang="th">{dept_info['name_th']}</rdfs:label>
        <rdfs:label xml:lang="en">{dept_info['name_en']}</rdfs:label>
    </owl:NamedIndividual>

"""

    for symp_id, symp_info in SYMPTOMS_DATA.items():
        ttl_content += f"""    <owl:NamedIndividual rdf:about="http://www.semanticweb.org/204424/TPHSRS/{symp_id}">
        <rdf:type rdf:resource="http://www.semanticweb.org/204424/TPHSRS/Symptom"/>
        <suggestsDepartment rdf:resource="http://www.semanticweb.org/204424/TPHSRS/{symp_info['department']}"/>
        <hasDescription>{symp_info['description']}</hasDescription>
        <severityLevel>{symp_info['severity']}</severityLevel>
        <rdfs:label xml:lang="th">{symp_info['name_th']}</rdfs:label>
        <rdfs:label xml:lang="en">{symp_info['name_en']}</rdfs:label>
    </owl:NamedIndividual>

"""

    for _, hospital in df_hospitals.iterrows():
        hospital_id = hospital['hospital_name_en'].replace(' ', '').replace('-', '')
        hospital_type = hospital['hospital_type']
        
        ttl_content += f"""    <owl:NamedIndividual rdf:about="http://www.semanticweb.org/204424/TPHSRS/{hospital_id}">
        <rdf:type rdf:resource="http://www.semanticweb.org/204424/TPHSRS/{hospital_type}"/>
"""
        
        if hospital['accepts_universal_coverage'] == 1:
            ttl_content += """        <acceptsRight rdf:resource="http://www.semanticweb.org/204424/TPHSRS/GoldCard"/>
"""
        if hospital['accepts_social_security'] == 1:
            ttl_content += """        <acceptsRight rdf:resource="http://www.semanticweb.org/204424/TPHSRS/SocialSecurity"/>
"""
        if hospital['accepts_civil_servant'] == 1:
            ttl_content += """        <acceptsRight rdf:resource="http://www.semanticweb.org/204424/TPHSRS/CivilServant"/>
"""
        
        ttl_content += f"""        <hasPhoneNumber>{hospital['phone']}</hasPhoneNumber>
        <hasEmergencyNumber>{hospital['emergency_phone']}</hasEmergencyNumber>
        <locationProvince>{hospital['province']}</locationProvince>
        <locationRegion>{hospital['region']}</locationRegion>
        <hasAddress>{hospital['address']}</hasAddress>
        <hasWebsite>{hospital['website']}</hasWebsite>
        <numberOfBeds rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">{hospital['beds']}</numberOfBeds>
        <latitude rdf:datatype="http://www.w3.org/2001/XMLSchema#float">{hospital['latitude']}</latitude>
        <longitude rdf:datatype="http://www.w3.org/2001/XMLSchema#float">{hospital['longitude']}</longitude>
        <hospitalCode>{hospital['hospital_code']}</hospitalCode>
        <rdfs:label xml:lang="th">{hospital['hospital_name_th']}</rdfs:label>
        <rdfs:label xml:lang="en">{hospital['hospital_name_en']}</rdfs:label>
    </owl:NamedIndividual>

"""
    
    ttl_content += "</rdf:RDF>"
    return ttl_content

def main():
    print("=" * 60)
    print("TPHSRS Data Loader - Thai Government Hospital Data")
    print("=" * 60)
    print()
    
    from io import StringIO
    df_hospitals = pd.read_csv(StringIO(SAMPLE_THAI_HOSPITALS_DATA))
    
    print(f"✅ โหลดข้อมูลโรงพยาบาล: {len(df_hospitals)} แห่ง")
    print(f"   - โรงพยาบาลรัฐ: {len(df_hospitals[df_hospitals['hospital_type'] == 'PublicHospital'])} แห่ง")
    print(f"   - โรงพยาบาลเอกชน: {len(df_hospitals[df_hospitals['hospital_type'] == 'PrivateHospital'])} แห่ง")
    print()
    print(f"✅ โหลดข้อมูลแผนก: {len(DEPARTMENTS_DATA)} แผนก")
    print(f"✅ โหลดข้อมูลอาการ: {len(SYMPTOMS_DATA)} อาการ")
    print()
    
    ttl_content = generate_ttl_ontology(df_hospitals)
    
    output_file = "TPHSRS-Government-Data.ttl"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(ttl_content)
    
    print(f"✅ สร้างไฟล์ Ontology: {output_file}")
    print(f"   ขนาดไฟล์: {len(ttl_content)} bytes")
    print()
    
    stats = {
        "total_hospitals": len(df_hospitals),
        "public_hospitals": len(df_hospitals[df_hospitals['hospital_type'] == 'PublicHospital']),
        "private_hospitals": len(df_hospitals[df_hospitals['hospital_type'] == 'PrivateHospital']),
        "departments": len(DEPARTMENTS_DATA),
        "symptoms": len(SYMPTOMS_DATA),
        "provinces": df_hospitals['province'].nunique(),
        "regions": df_hospitals['region'].nunique()
    }
    
    stats_file = "TPHSRS-Stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"✅ สร้างไฟล์สถิติ: {stats_file}")
    print()
    print("📊 สถิติข้อมูล:")
    print(f"   - โรงพยาบาลทั้งหมด: {stats['total_hospitals']} แห่ง")
    print(f"   - จังหวัด: {stats['provinces']} จังหวัด")
    print(f"   - ภูมิภาค: {stats['regions']} ภูมิภาค")
    print(f"   - แผนก: {stats['departments']} แผนก")
    print(f"   - อาการ: {stats['symptoms']} อาการ")
    print()
    print("=" * 60)
    print("✅ เสร็จสมบูรณ์!")
    print("=" * 60)
    print()
    print("📁 ไฟล์ที่สร้าง:")
    print(f"   1. {output_file}")
    print(f"   2. {stats_file}")
    print()
    print("🚀 พร้อมใช้งานกับ Protégé!")

if __name__ == "__main__":
    main()
