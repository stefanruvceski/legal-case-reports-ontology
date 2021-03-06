# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 00:22:55 2020

@author: Marko Pejić
"""


import owlready2
from owlready2 import onto_path
from owlready2 import get_ontology
from owlready2 import sync_reasoner
import pandas as pd
import numpy as np
from datetime import datetime

# za HermiT reasoner
owlready2.JAVA_EXE = 'C:/Program Files/Java/jdk-14.0.1/bin/java.exe'


class LCRDataWrapper:    
    def __init__(self, data_row):
        self.case_id = data_row['case_id']
        self.case_name = data_row['case_name']
        self.judgement_date = datetime.strptime(data_row['judgement_date'], '%Y-%m-%d').date()
        self.hearing_date = datetime.strptime(data_row['hearing_date'], '%Y-%m-%d').date()
        self.judgement_registry = data_row['judgement_registry']
        self.jurisdiction_court = data_row['jurisdiction_court']
        self.jurisdiction_court_city = data_row['jurisdiction_court_city']
        self.judge = data_row['judge']
        
        if(data_row['side1_counsel'] != ''):
            self.side1_counsels = data_row['side1_counsel'].split(';')
        else:
            self.side1_counsels = []
            
        if(data_row['side1_solicitor'] != ''):
            self.side1_solicitors = data_row['side1_solicitor'].split(';')
        else:
            self.side1_solicitors = []
        
        if(data_row['side2_counsel'] != ''):
            self.side2_counsels = data_row['side2_counsel'].split(';')
        else:
            self.side2_counsels = []
            
        if(data_row['side2_solicitor']):
            self.side2_solicitors = data_row['side2_solicitor'].split(';')
        else:
            self.side2_solicitors = []
            
        self.side1_role = data_row['side1_role']     # ne znam kakvih jos ima uloga, video sam i applicant
        
        # moze da bude vise ucesnika na prvoj strani, ali svi su u istoj ulozi
        if(data_row['side1'] != ''):
            self.side1 = data_row['side1'].split(';')
        else:
            self.side1 = []
        
        self.side2_role = data_row['side2_role']        # ima vise uloga, nije jedina respondent
        
        # moze da bude vise ucesnika na drugoj strani, proveriti da li isto vazi i za prvu
        if(data_row['side2'] != ''):
            self.side2 = data_row['side2'].split(';')
        else:
            self.side2 = []
            
        if(data_row['legal_rules'] != ''):
            self.legal_rules = data_row['legal_rules'].split(';')
        else:
            self.legal_rules = []
        
        # druge presude koje referencira trenutna presuda!!!
        if(data_row['referenced_cases'] != ''):
            self.referenced_cases = data_row['referenced_cases'].split(';')
        else:
            self.referenced_cases = []
        
        # imena presuda koje referencira trenutna presuda
        if(data_row['ref_names'] != ''):
            self.ref_names = data_row['ref_names'].split(';')
        else:
            self.ref_names = []

# Funkcija ucitava csv fajl i kreira listu wrapper objekata od kojih ce se populisati ontologija
def load_data(path='lcr_data.csv'):
    data = []
    
    df = pd.read_csv(path, index_col=False)
    df = df.replace(np.nan, '', regex=True)         # replace missing values with empty string
    
    for index, row in df.iterrows():
        data.append(LCRDataWrapper(row))
        
    return data

def load_ontology():
    print('Ontology loading...')
    onto_path.append('ontology/')
    onto_path.append('ontology/judo-master')
    onto_path.append('ontology/lkif-core-master/')
    onto = get_ontology('http://www.semanticweb.org/marko/ontologies/2020/3/lcr_onto.owl').load()
    
    return onto

def populate_ontology(legal_ontology, data_instances):
    # imported ontologies
    ontologies = list(legal_ontology.imported_ontologies)
    judo = list(ontologies[0].imported_ontologies)[0]
    lkif_role = ontologies[1]
    lkif_action = lkif_role.get_namespace('http://www.estrellaproject.org/lkif-core/action.owl#')
    lkif_legal_action = lkif_role.get_namespace('http://www.estrellaproject.org/lkif-core/legal-action.owl#')
    lkif_top = lkif_role.get_namespace('http://www.estrellaproject.org/lkif-core/lkif-top.owl#')
    lkif_legal_role = lkif_role.get_namespace('http://www.estrellaproject.org/lkif-core/legal-role.owl#')
    lkif_process = lkif_role.get_namespace('http://www.estrellaproject.org/lkif-core/process.owl#')
    
    for instance in data_instances:
        # Jurisdiction individual
        court = instance.jurisdiction_court.replace(' ', '_')
        jurisdiction = judo.Jurisdiction(court, namespace=legal_ontology)
        
        # Judgement individual
        judgement = instance.case_id.replace(' ', '_')
        judgement = judo.Judgement(judgement, namespace=legal_ontology)
        judgement.judgement_name.append(instance.case_name)
        judgement.jurisdiction_city.append(instance.jurisdiction_court_city)
        judgement.judgement_date.append(instance.judgement_date)
        judgement.hearing_date.append(instance.hearing_date)
        # spajanje suda i presude preko considered_by ObjectProperty-a
        judgement.considered_by.append(jurisdiction)
        
        # Registry individual
        registry_name = instance.judgement_registry.replace(' ', '_')
        registry = lkif_process.Physical_Object(registry_name, namespace=legal_ontology)
        registry.stores.append(judgement)         # dodavanje dokumenta u odgovarajuci registry
        
        # svi ucesnici presude modelovani su kao Legal_Person, jer ne moraju biti iskljucivo jedna osoba, vec mogu biti i kompanije, organizacije, itd.
        
        # Judge individual (Legal_Person that %plays% "judge" Legal_Role)
        # takodje je ucesnik odgovarajuce presude, tj. .participant(...presuda...)
        judge_name = instance.judge.replace(' ', '_')
        judge = lkif_legal_action.Legal_Person(judge_name, namespace=legal_ontology)
        judge_role = lkif_legal_role.Legal_Role('judge', namespace=legal_ontology)
        judge.plays.append(judge_role)
        judge.participant.append(judgement)
        
        # Side 1 (Appellant/Applicant) Counsel individual
        for counsel in instance.side1_counsels:
            a_counsel_name = counsel.replace(' ', '_')
            side1_counsel = lkif_legal_action.Legal_Person(a_counsel_name, namespace=legal_ontology)
            side1_counsel_role = lkif_legal_role.Legal_Role(instance.side1_role + '_counsel', namespace=legal_ontology)
            side1_counsel.plays.append(side1_counsel_role)
            side1_counsel.participant.append(judgement)
        
        # Side 1 Solicitor individual
        for solicitor in instance.side1_solicitors:
            a_solicitor_name = solicitor.replace(' ', '_')
            side1_solicitor = lkif_legal_action.Legal_Person(a_solicitor_name, namespace=legal_ontology)
            side1_solicitor_role = lkif_legal_role.Legal_Role(instance.side1_role + '_solicitor', namespace=legal_ontology)
            side1_solicitor.plays.append(side1_solicitor_role)
            side1_solicitor.participant.append(judgement)
            
        # Side 2 Counsel individual
        for counsel in instance.side2_counsels:
            r_counsel_name = counsel.replace(' ', '_')
            side2_counsel = lkif_legal_action.Legal_Person(r_counsel_name, namespace=legal_ontology)
            side2_counsel_role = lkif_legal_role.Legal_Role(instance.side2_role + '_counsel', namespace=legal_ontology)
            side2_counsel.plays.append(side2_counsel_role)
            side2_counsel.participant.append(judgement)
            
        # Side 2 Solicitor individual
        for solicitor in instance.side2_solicitors:
            r_solicitor_name = solicitor.replace(' ', '_')
            side2_solicitor = lkif_legal_action.Legal_Person(r_solicitor_name, namespace=legal_ontology)
            side2_solicitor_role = lkif_legal_role.Legal_Role(instance.side2_role + '_solicitor', namespace=legal_ontology)
            side2_solicitor.plays.append(side2_solicitor_role)
            side2_solicitor.participant.append(judgement)
            
        # Side 1 individual (left of V in judgement full name)
        for side1_name in instance.side1:
            side1_name = side1_name.replace(' ', '_')
            side1 = lkif_legal_action.Legal_Person(side1_name, namespace=legal_ontology)
            side1_role = lkif_legal_role.Legal_Role(instance.side1_role, namespace=legal_ontology)
            side1.plays.append(side1_role)
            side1.participant.append(judgement)
        
        # Side 2 individuals (right of V in judgement full name)
        # There could be more than 1 respondents!
        for side2_name in instance.side2:
            side2_name = side2_name.replace(' ', '_')
            side2 = lkif_legal_action.Legal_Person(side2_name, namespace=legal_ontology)
            side2_role = lkif_legal_role.Legal_Role(instance.side2_role, namespace=legal_ontology)    # proveriti da li postoji vise razlicitih uloga!
            side2.plays.append(side2_role)
            side2.participant.append(judgement)
        
        # Legal rule individuals
        for rule in instance.legal_rules:
            rule = rule.replace(' ', '_')
            legal_rule = judo.Legal_Rule(rule, namespace=legal_ontology)
            judgement.considers.append(legal_rule)
            
        # Referencirane presude
        for ref_case, ref_name in zip(instance.referenced_cases, instance.ref_names):
            # pravljenje individuala presude koja se referencira (VIDI STA SE DESAVA AKO TAKAV INDIVIDUAL VEC POSTOJI)
            ref_case = ref_case.replace(' ', '_')
            ref_judgement = judo.Judgement(ref_case, namespace=legal_ontology)
            ref_judgement.judgement_name.append(ref_name)
            # aktuelna presuda -> considers -> referencirana presuda
            judgement.considers.append(ref_judgement)
           
    # HermiT reasoner -> ako bude pucalo, skines HermiT sa zvanicnog sajta, raspakujes i zamenis to sa onim sto ti je instalirano preko owlready2
    # znaci bice negde ili AppData/Python/... ili u okruzenju koje koristis u anakondi
    # pretrazi onim fensi search everything pa vidi gde je
    with legal_ontology:
        sync_reasoner(infer_property_values=True)
        
    save_ontology(legal_ontology)
    
def save_ontology(legal_ontology):
    legal_ontology.save()

# privremeno samo, lakse mi je ovako napraviti csv nego da kuckam po nekom fajlu
# sad u ovaj csv redom dodavati podatke za svaki dokument (rucno ili automatski, zavisi koliko toga mozemo kroz kod)
# ako bude rucno, otvoris u excelu i redom, brzo ce to ici, nema ispod trocifrenog broja dokumenata
# FUNKCIJA VISE NE SLUZI NICEMU I NE TREBA JE KORISTITI
"""def initiate_data():
    case_id = '[2006] FCA 35'
    judgement_date = '6 February 2006'
    hearing_date = '21 November 2005'
    judgement_registry = 'New South Wales District Registry'
    jurisdiction_court = 'Federal Court of Australia'
    jurisdiction_court_city = 'Sydney'
    judge = 'Moore J'
    side1_counsel = ''
    side1_solicitor = 'Michael Jones'
    respondent_counsel = 'S LLoyd'
    respondent_solicitor = 'Clayton Utz'
    side1_role = 'appellant'     # ne znam kakvih jos ima uloga, video sam i applicant
    side1 = 'SZGBY'
    # moze da bude vise ucesnika na drugoj strani, proveriti da li isto vazi i za prvu
    # OVE PODATKE KOJI TREBAJU DA BUDU CUVATI SA ';' KAO SEPARATOROM!!!!
    side2 = 'Minister for Immigration and Multicultural and Indigenous Affairs;Refugee Review Tribunal'
    legal_rules = 'Migration Act 1958'      # ovde isto treba ';', samo je sad jedan pa nema potrebe!!!
    
    data = []
    data.append([case_id, judgement_date, hearing_date, judgement_registry, jurisdiction_court,
                 jurisdiction_court_city, judge, side1_counsel, side1_solicitor, respondent_counsel,
                 respondent_solicitor, side1_role, side1, side2, legal_rules])
      
    df = pd.DataFrame(data, columns=['case_id', 'judgement_date', 'hearing_date', 'judgement_registry', 'jurisdiction_court', 'jurisdiction_court_city', 'judge', 'side1_counsel', 'side1_solicitor', 'respondent_counsel', 'respondent_solicitor', 'side1_role', 'side1', 'side2', 'legal_rules'])
    
    df.to_csv('lcr_data.csv', index=False)"""


#initiate_data()
data = load_data()

lcr_ontology = load_ontology()
# test nad dokumentom 06_35
#doc6_35 = LCRDataWrapper()
#data = [doc6_35]
populate_ontology(lcr_ontology, data)





