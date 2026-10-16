"""Search terms for Line 5, access and educational trajectories.

These are the exact terms registered in the Query strings field of the OSF
registration. Three rules apply to this file:

1. One phrase per line. The World Bank interface needs each phrase on its
   own, and one phrase per line makes a change show up cleanly in git.
2. Straight quotes. The registration shows typographic quotes because it is
   prose. The APIs need straight quotes to match a phrase.
3. The order of the terms is the registered order, accented forms first and
   accent-free forms at the end of each block. Do not reorder them.
"""

LINE = "line5"
LINE_LABEL = "Access and educational trajectories"

SUBINTERVENTIONS = {
    "scholarships_and_student_grants": {
        "label": "Scholarships and student grants",
        "en": [
            "scholarship",
            "scholarships",
            "stipend",
            "stipends",
            "bursary",
            "bursaries",
            "student grant",
            "student grants",
            "education grant",
            "education grants",
            "student financial aid",
            "tuition waiver",
            "tuition waivers",
            "fee waiver",
            "fee waivers",
            "school fee exemption",
            "school fee reduction",
            "school fee abolition",
            "abolition of school fees",
            "free tuition",
            "tuition-free",
            "education subsidy",
            "education subsidies",
        ],
        "es": [
            "beca escolar",
            "becas escolares",
            "beca estudiantil",
            "becas estudiantiles",
            "beca de estudio",
            "becas de estudio",
            "subsidio educativo",
            "subsidios educativos",
            "subsidio escolar",
            "subsidios escolares",
            "ayuda financiera estudiantil",
            "exención de matrícula",
            "exencion de matricula",
        ],
        "pt": [
            "bolsa de estudo",
            "bolsas de estudo",
            "bolsa estudantil",
            "bolsas estudantis",
            "auxílio estudantil",
            "subsídio educacional",
            "subsídios educacionais",
            "isenção de mensalidade",
            "isenção de taxas escolares",
            "auxilio estudantil",
            "subsidio educacional",
            "subsidios educacionais",
            "isencao de mensalidade",
            "isencao de taxas escolares",
        ],
    },
    
        "school_feeding": {
        "label": "School feeding",
        "en": [
            "school feeding",
            "food for education",
            "school meal",
            "school meals",
            "midday meal",
            "midday meals",
            "mid-day meal",
            "mid-day meals",
            "school lunch",
            "school lunches",
            "school breakfast",
            "take-home ration",
            "take-home rations",
            "feeding program",
            "feeding programs",
            "feeding programme",
            "feeding programmes",
        ],
        "es": [
            "alimentación escolar",
            "comedor escolar",
            "comedores escolares",
            "almuerzo escolar",
            "almuerzos escolares",
            "desayuno escolar",
            "desayunos escolares",
            "merienda escolar",
            "meriendas escolares",
            "refrigerio escolar",
            "refrigerios escolares",
            "colación escolar",
            "colaciones escolares",
            "programa de alimentación escolar",
            "programas de alimentación escolar",
            "alimentacion escolar",
            "colacion escolar",
            "programa de alimentacion escolar",
            "programas de alimentacion escolar",
        ],
        "pt": [
            "alimentação escolar",
            "merenda escolar",
            "refeição escolar",
            "refeições escolares",
            "lanche escolar",
            "programa de alimentação escolar",
            "programas de alimentação escolar",
            "alimentacao escolar",
            "refeicao escolar",
            "refeicoes escolares",
            "programa de alimentacao escolar",
            "programas de alimentacao escolar",
        ],
    },
            "dropout_prevention": {
        "label": "Dropout prevention",
        "en": [
            "dropout prevention",
            "drop-out prevention",
            "dropout reduction",
            "early school leaving",
            "preventing early school leaving",
            "school reintegration",
            "re-enrolment",
            "re-enrollment",
            "second chance education",
            "second-chance education",
            "school re-entry",
        ],
        "es": [
            "prevención de la deserción escolar",
            "reducción de la deserción escolar",
            "prevención del abandono escolar",
            "retención escolar",
            "permanencia escolar",
            "reinserción escolar",
            "revinculación escolar",
            "prevencion de la desercion escolar",
            "reduccion de la desercion escolar",
            "prevencion del abandono escolar",
            "retencion escolar",
            "reinsercion escolar",
            "revinculacion escolar",
        ],
        "pt": [
            "prevenção da evasão escolar",
            "combate à evasão escolar",
            "prevenção do abandono escolar",
            "permanência escolar",
            "reinserção escolar",
            "reintegração escolar",
            "prevencao da evasao escolar",
            "combate a evasao escolar",
            "prevencao do abandono escolar",
            "permanencia escolar",
            "reinsercao escolar",
            "reintegracao escolar",
        ],
    },
            
        "early_warning_systems": {
        "label": "Early-warning systems",
        "en": [
            "early warning system",
            "early warning systems",
            "early-warning system",
            "early-warning systems",
            "early warning indicator",
            "early warning indicators",
            "early alert system",
            "dropout prediction",
            "predicting dropout",
            "identification of at-risk students",
        ],
        "es": [
            "sistema de alerta temprana",
            "sistemas de alerta temprana",
            "alerta temprana escolar",
            "indicadores de alerta temprana",
            "predicción de la deserción",
            "identificación de estudiantes en riesgo",
            "prediccion de la desercion",
            "identificacion de estudiantes en riesgo",
        ],
        "pt": [
            "sistema de alerta precoce",
            "sistemas de alerta precoce",
            "indicadores de alerta precoce",
            "previsão de evasão",
            "identificação de alunos em risco",
            "previsao de evasao",
            "identificacao de alunos em risco",
        ],
    },
        
    "remediation": {
        "label": "Remediation",
        "en": [
            "remedial education",
            "remedial instruction",
            "remedial program",
            "remedial programs",
            "remedial programme",
            "remedial programmes",
            "catch-up program",
            "catch-up programme",
            "accelerated learning program",
            "accelerated learning programme",
            "accelerated education",
            "learning recovery",
        ],
        "es": [
            "refuerzo escolar",
            "clases de refuerzo",
            "nivelación escolar",
            "nivelación académica",
            "programa de nivelación",
            "recuperación de aprendizajes",
            "recuperación pedagógica",
            "aceleración del aprendizaje",
            "nivelacion escolar",
            "nivelacion academica",
            "programa de nivelacion",
            "recuperacion de aprendizajes",
            "recuperacion pedagogica",
            "aceleracion del aprendizaje",
        ],
        "pt": [
            "reforço escolar",
            "aulas de reforço",
            "recuperação escolar",
            "recuperação de aprendizagem",
            "aceleração da aprendizagem",
            "correção de fluxo",
            "recomposição de aprendizagens",
            "reforco escolar",
            "aulas de reforco",
            "recuperacao escolar",
            "recuperacao de aprendizagem",
            "aceleracao da aprendizagem",
            "correcao de fluxo",
            "recomposicao de aprendizagens",
        ],
    },
    
        "school_transportation": {
        "label": "School transportation",
        "en": [
            "school transportation",
            "school transport",
            "student transport",
            "transport subsidy",
            "transport subsidies",
            "school bus",
            "school buses",
            "bicycle program",
            "bicycle programme",
            "bicycle distribution",
            "bicycle provision",
        ],
        "es": [
            "transporte escolar",
            "transporte estudiantil",
            "subsidio de transporte escolar",
            "ruta escolar",
            "rutas escolares",
            "bus escolar",
            "buses escolares",
            "distribución de bicicletas",
            "bicicletas escolares",
            "distribucion de bicicletas",
        ],
        "pt": [
            "transporte escolar",
            "transporte estudantil",
            "ônibus escolar",
            "ônibus escolares",
            "distribuição de bicicletas",
            "bicicletas escolares",
            "onibus escolar",
            "onibus escolares",
            "distribuicao de bicicletas",
        ],
    },
        
        "extended_school_day": {
        "label": "Extended school day",
        "en": [
            "extended school day",
            "full-day school",
            "full day school",
            "full-day schooling",
            "longer school day",
            "extended learning time",
            "expanded learning time",
            "extended-day program",
            "double-shift school",
            "double-shift schooling",
        ],
        "es": [
            "jornada escolar extendida",
            "jornada escolar completa",
            "jornada escolar única",
            "escuela de tiempo completo",
            "escuelas de tiempo completo",
            "ampliación de la jornada escolar",
            "jornada escolar unica",
            "ampliacion de la jornada escolar",
        ],
        "pt": [
            "escola de tempo integral",
            "educação em tempo integral",
            "ensino em tempo integral",
            "jornada escolar ampliada",
            "ampliação da jornada escolar",
            "educacao em tempo integral",
            "ampliacao da jornada escolar",
        ],
    },
        
        "career_counseling_and_guidance": {
        "label": "Career counseling and guidance",
        "en": [
            "career counseling",
            "career counselling",
            "career guidance",
            "vocational guidance",
            "career orientation",
            "career education",
            "college counseling",
            "college counselling",
            "guidance counseling",
            "guidance counselling",
        ],
        "es": [
            "orientación vocacional",
            "orientación profesional",
            "orientación educativa",
            "orientacion vocacional",
            "orientacion profesional",
            "orientacion educativa",
        ],
        "pt": [
            "orientação vocacional",
            "orientação profissional",
            "orientação de carreira",
            "aconselhamento vocacional",
            "orientacao vocacional",
            "orientacao profissional",
            "orientacao de carreira",
        ],
    },
        
        "transition_support_programs": {
        "label": "Transition support programs",
        "en": [
            "school transition program",
            "school transition programme",
            "transition to secondary school",
            "primary to secondary transition",
            "bridging program",
            "bridging programme",
        ],
        "es": [
            "transición de primaria a secundaria",
            "articulación primaria-secundaria",
            "programa de transición escolar",
            "transicion de primaria a secundaria",
            "articulacion primaria-secundaria",
            "programa de transicion escolar",
        ],
        "pt": [
            "transição do fundamental para o médio",
            "programa de transição escolar",
            "transicao do fundamental para o medio",
            "programa de transicao escolar",
        ],
    },
}


#LANGUAGES = ("en", "es", "pt")

#if __name__ == "__main__":
 #   for key, block in SUBINTERVENTIONS.items():
  #      counts = ", ".join(f"{lang} {len(block[lang])}" for lang in LANGUAGES)
#     print(f"{block['label']}: {counts}")

LANGUAGES = ("en", "es", "pt")


def iter_blocks():
    """Yield one block per sub-intervention and language.

    A block is what the registration calls a query: the terms of one
    sub-intervention in one language. The search script joins them with OR
    for OpenAlex and ERIC, and sends them one phrase at a time to the World
    Bank. Yielding them from here keeps the search script from having to
    know how this file is organised, so a new line only needs a new terms
    file and no change to the search script.
    """
    for key, block in SUBINTERVENTIONS.items():
        for language in LANGUAGES:
            yield {
                "line": LINE,
                "subintervention": key,
                "subintervention_label": block["label"],
                "language": language,
                "terms": block[language],
            }


if __name__ == "__main__":
    total = 0
    for key, block in SUBINTERVENTIONS.items():
        counts = ", ".join(f"{lang} {len(block[lang])}" for lang in LANGUAGES)
        subtotal = sum(len(block[lang]) for lang in LANGUAGES)
        total += subtotal
        print(f"{block['label']:<35} {counts:<22} total {subtotal}")
    print(f"\n{len(SUBINTERVENTIONS)} sub-interventions, "
          f"{len(list(iter_blocks()))} blocks, {total} phrases")
    
    
