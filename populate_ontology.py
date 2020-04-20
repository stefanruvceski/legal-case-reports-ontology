# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 00:22:55 2020

@author: Marko Pejić
"""


import owlready2
from owlready2 import onto_path
from owlready2 import get_ontology
from owlready2 import sync_reasoner

# za HermiT reasoner
owlready2.JAVA_EXE = 'C:/Program Files/Java/jdk-14.0.1/bin/java.exe'


# ovo cemo koristiti za prosledjivanje podataka do ontologije
# napravicemo CSV ili JSON sa atributima istim kao i polja ove klase, gde ce svaki red predstavljati po jedan dokument koji obradimo
# i onda cemo funkciji za populisanje ontologije prosledjivati listu objekata ove klase, koju cemo dobiti ucitavanjem CSV ili JSON dokumenta
class LCRDataWrapper:
    # privremeni konstruktor, sluzi samo za testiranje nad jednim dokumentom
    def __init__(self):
        # u originalu je [2006] FCA 35
        # treba replace-ovati razmake sa '_' -> mislim da samo kod stringova koji ce biti name individuala u ontologiji, tj. ono sto prosledjujem kroz konstruktor
        # za sad ja to replace-ujem kad populisem ontologiju, tako da je to okej
        self.case_id = '[2006] FCA 35'
        self.judgement_date = '6 February 2006'
        self.hearing_date = '21 November 2005'
        self.judgement_registry = 'New South Wales District Registry'
        self.jurisdiction_court = 'Federal Court of Australia'
        self.jurisdiction_court_city = 'Sydney'
        self.judge = 'Moore J'
        self.side1_counsel = ''
        self.side1_solicitor = 'Michael Jones'
        self.respondent_counsel = 'S LLoyd'
        self.respondent_solicitor = 'Clayton Utz'
        self.side1_role = 'appellant'     # ne znam kakvih jos ima uloga, video sam i applicant
        self.side1 = 'SZGBY'
        # moze da bude vise ucesnika na drugoj strani, proveriti da li isto vazi i za prvu
        self.side2 = ['Minister for Immigration and Multicultural and Indigenous Affairs', 'Refugee Review Tribunal']
        self.legal_rules = ['Migration Act 1958']
    
    """def __init__(self, data_row):
        self.case_id = data_row.case_id
        self.judgement_date = data_row.judgement_date
        self.hearing_date = data_row.hearing_date
        self.judgement_registry = data_row.judgement_registry"""
        # .... TODO


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
        jurisdiction.jurisdiction_city.append(instance.jurisdiction_court_city)
        
        # Judgement individual
        judgement = instance.case_id.replace(' ', '_')
        judgement = judo.Judgement(judgement, namespace=legal_ontology)
        judgement.judgement_date.append(instance.judgement_date)
        judgement.hearing_date.append(instance.hearing_date)
        # spajanje suda i presude preko considered_by ObjectProperty-a
        judgement.considered_by.append(jurisdiction)
        
        # Registry individual
        registry_name = instance.judgement_registry.replace(' ', '_')
        registry = lkif_process.Physical_Object(registry_name, namespace=legal_ontology)
        registry.stores.append(judgement)         # dodavanje dokumenta u odgovarajuci registry
        
        # Judge individual (Person that %plays% "judge" Legal_Role)
        # takodje je ucesnik odgovarajuce presude, tj. .participant(...presuda...)
        judge_name = instance.judge.replace(' ', '_')
        judge = lkif_action.Person(judge_name, namespace=legal_ontology)
        judge_role = lkif_legal_role.Legal_Role('judge', namespace=legal_ontology)
        judge.plays.append(judge_role)
        judge.participant.append(judgement)
        
        # Side1 (Appellant/Applicant) Counsel individual
        if(instance.side1_counsel != ''):
            a_counsel_name = instance.side1_counsel.replace(' ', '_')
            side1_counsel = lkif_action.Person(a_counsel_name, namespace=legal_ontology)
            side1_counsel_role = lkif_legal_role.Legal_Role(instance.side1_role + '_counsel', namespace=legal_ontology)
            side1_counsel.plays.append(side1_counsel_role)
            side1_counsel.participant.append(judgement)
        
        # Appellant Solicitor individual
        if(instance.side1_solicitor != ''):
            a_solicitor_name = instance.side1_solicitor.replace(' ', '_')
            side1_solicitor = lkif_action.Person(a_solicitor_name, namespace=legal_ontology)
            side1_solicitor_role = lkif_legal_role.Legal_Role(instance.side1_role + '_solicitor', namespace=legal_ontology)
            side1_solicitor.plays.append(side1_solicitor_role)
            side1_solicitor.participant.append(judgement)
            
        # Respondent Counsel individual
        if(instance.respondent_counsel != ''):
            r_counsel_name = instance.respondent_counsel.replace(' ', '_')
            respondent_counsel = lkif_action.Person(r_counsel_name, namespace=legal_ontology)
            respondent_counsel_role = lkif_legal_role.Legal_Role('respondent_counsel', namespace=legal_ontology)
            respondent_counsel.plays.append(respondent_counsel_role)
            respondent_counsel.participant.append(judgement)
            
        # Respondent Solicitor individual
        if(instance.respondent_solicitor != ''):
            r_solicitor_name = instance.respondent_solicitor.replace(' ', '_')
            respondent_solicitor = lkif_action.Person(r_solicitor_name, namespace=legal_ontology)
            respondent_solicitor_role = lkif_legal_role.Legal_Role('respondent_solicitor', namespace=legal_ontology)
            respondent_solicitor.plays.append(respondent_solicitor_role)
            respondent_solicitor.participant.append(judgement)
            
        # Side 1 individual (left of V in judgement full name)
        side1_name = instance.side1.replace(' ', '_')
        side1 = lkif_legal_action.Legal_Person(side1_name, namespace=legal_ontology)
        side1_role = lkif_legal_role.Legal_Role(instance.side1_role, namespace=legal_ontology)
        side1.plays.append(side1_role)
        side1.participant.append(judgement)
        
        # Side 2 individuals (right of V in judgement full name)
        # There could be more than 1 respondents!
        for side2_name in instance.side2:
            side2_name = side2_name.replace(' ', '_')
            side2 = lkif_legal_action.Legal_Person(side2_name, namespace=legal_ontology)
            side2_role = lkif_legal_role.Legal_Role('respondent', namespace=legal_ontology)    # proveriti da li postoji vise razlicitih uloga!
            side2.plays.append(side2_role)
            side2.participant.append(judgement)
        
        # Legal rule individuals
        for rule in instance.legal_rules:
            rule = rule.replace(' ', '_')
            legal_rule = judo.Legal_Rule(rule, namespace=legal_ontology)
            judgement.considers.append(legal_rule)
           
    # HermiT reasoner -> ako bude pucalo, skines HermiT sa zvanicnog sajta, raspakujes i zamenis to sa onim sto ti je instalirano preko owlready2
    # znaci bice negde ili AppData/Python/... ili u okruzenju koje koristis u anakondi
    # pretrazi onim fensi search everything pa vidi gde je
    with legal_ontology:
        sync_reasoner(infer_property_values=True)
        
    save_ontology(legal_ontology)
    
def save_ontology(legal_ontology):
    legal_ontology.save()


lcr_ontology = load_ontology()
# test nad dokumentom 06_35
doc6_35 = LCRDataWrapper()
data = [doc6_35]
populate_ontology(lcr_ontology, data)

print(list(list(lcr_ontology.imported_ontologies)[1].classes()))

#namespace = lkif.get_namespace('http://www.estrellaproject.org/lkif-core/action.owl#')
#namespace.Person()
    
    
    
    
    
