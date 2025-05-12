Map<String, Map<String, dynamic>> testSequence() {
  return {
    "Fall2025": {
      "courses": ["CIIC4010", "INGE3035", "QUIM3132", "QUIM3134", "CHIN3051"],
      "difficulty": 85
    },
    "Spring2026": {
      "courses": ["CIIC4010", "INGE3035", "QUIM3132", "QUIM3134", "CHIN3051"],
      "difficulty": 94
    }
  };
}

Map<String, Map<String, dynamic>> testCourses() {
  return {
    "CIIC4010": {
      "prerequisites": ["CIIC3015"],
      "corequisites": [],
      "prerequisite_for": ["CIIC4020"],
      "corequisite_for": []
    },
    "INGE3035": {
      "prerequisites": ["CIIC3015"],
      "corequisites": [],
      "prerequisite_for": [],
      "corequisite_for": []
    },
    "QUIM3132": {
      "prerequisites": ["QUIM3131", "QUIM3133"],
      "corequisites": ["QUIM3134"],
      "prerequisite_for": ["INGE3035"],
      "corequisite_for": []
    },
    "QUIM3134": {
      "prerequisites": ["QUIM3131", "QUIM3133"],
      "corequisites": [],
      "prerequisite_for": ["INGE3035"],
      "corequisite_for": ["QUIM3132"]
    },
    "CHIN3051": {
      "prerequisites": [],
      "corequisites": [],
      "prerequisite_for": [],
      "corequisite_for": []
    },
  };
}

Map<String, dynamic> testRecommendationsOld() {
  return {
    "recommendations": [
      {
        "rank": 1,
        "score": 0.05445326278659612,
        "schedule_details": [
          {
            "term_name": "Fall 2026",
            "courses": [
              "MATE4145",
              "FISI3172",
              "CIIC5045",
              "CIIC4030",
              "CIIC4025",
              "CIIC4995",
              "INSO4998",
              "INSO4995",
              "INGL0066",
              "INGL6995",
              "INGL6999",
              "ESPA0041",
              "INGL6996",
              "MATE4050"
            ],
            "credits": 18,
            "difficulty_sum": 25
          },
          {
            "term_name": "Spring 2027",
            "courses": [
              "INME4045",
              "ININ4010",
              "ININ4015",
              "INSO4101",
              "FISI3174",
              "FISI3162",
              "FISI3164"
            ],
            "credits": 18,
            "difficulty_sum": 17
          },
          {
            "term_name": "Fall 2027",
            "courses": [
              "INGE3035",
              "FISI3161",
              "INGE3045",
              "INGE3011",
              "CIIC5110",
              "INSO4117"
            ],
            "credits": 18,
            "difficulty_sum": 13
          },
          {
            "term_name": "Spring 2028",
            "courses": [
              "CIIC5150",
              "INSO4116",
              "INSO4115",
              "CIIC5015",
              "INSO5111",
              "CIIC4998"
            ],
            "credits": 18,
            "difficulty_sum": 18
          },
          {
            "term_name": "Fall 2028",
            "courses": [
              "CIIC5019",
              "CIIC5995",
              "INGL3104",
              "ESPA3102",
              "INGL3101",
              "INGL4000"
            ],
            "credits": 18,
            "difficulty_sum": 13
          },
          {
            "term_name": "Spring 2029",
            "courses": [
              "INGL3205",
              "INGL3191",
              "INGL3225",
              "INGL3227",
              "INGL3231",
              "INGL3236"
            ],
            "credits": 18,
            "difficulty_sum": 12
          },
          {
            "term_name": "Fall 2029",
            "courses": [
              "INGL4255",
              "INGL4028",
              "INGL4075",
              "INGL4205",
              "INGL4208",
              "ESPA4012"
            ],
            "credits": 18,
            "difficulty_sum": 18
          },
          {
            "term_name": "Spring 2030",
            "courses": [
              "INGL4026",
              "INGL4030",
              "INGL4047",
              "INGL4125",
              "INGL4206",
              "ESPA4011"
            ],
            "credits": 18,
            "difficulty_sum": 18
          }
        ],
        "is_complete": false
      },
      {
        "rank": 2,
        "score": 0.05445326278659612,
        "schedule_details": [
          {
            "term_name": "Fall 2026",
            "courses": [
              "MATE4145",
              "FISI3172",
              "CIIC5045",
              "CIIC4030",
              "CIIC4025",
              "CIIC4995",
            ],
            "credits": 18,
            "difficulty_sum": 25
          },
          {
            "term_name": "Spring 2027",
            "courses": [
              "INME4045",
              "ININ4010",
              "ININ4015",
              "INSO4101",
              "FISI3174",
              "FISI3162",
              "FISI3164",
              "INSO4998",
              "INSO4995",
              "INGL0066",
              "INGL6995",
              "INGL6999",
              "ESPA0041",
              "INGL6996",
              "MATE4050"
            ],
            "credits": 18,
            "difficulty_sum": 17
          },
          {
            "term_name": "Fall 2027",
            "courses": [
              "INGE3035",
              "FISI3161",
              "INGE3045",
              "INGE3011",
              "CIIC5110",
              "INSO4117"
            ],
            "credits": 18,
            "difficulty_sum": 13
          },
          {
            "term_name": "Spring 2028",
            "courses": [
              "CIIC5150",
              "INSO4116",
              "INSO4115",
              "CIIC5015",
              "INSO5111",
              "CIIC4998"
            ],
            "credits": 18,
            "difficulty_sum": 18
          },
          {
            "term_name": "Fall 2028",
            "courses": [
              "CIIC5019",
              "CIIC5995",
              "INGL3104",
              "ESPA3102",
              "INGL3101",
              "INGL4000"
            ],
            "credits": 18,
            "difficulty_sum": 13
          },
          {
            "term_name": "Spring 2029",
            "courses": [
              "INGL3205",
              "INGL3191",
              "INGL3225",
              "INGL3227",
              "INGL3231",
              "INGL3236"
            ],
            "credits": 18,
            "difficulty_sum": 12
          },
          {
            "term_name": "Fall 2029",
            "courses": [
              "INGL4255",
              "INGL4028",
              "INGL4075",
              "INGL4205",
              "INGL4208",
              "ESPA4012"
            ],
            "credits": 18,
            "difficulty_sum": 18
          },
          {
            "term_name": "Spring 2030",
            "courses": [
              "INGL4026",
              "INGL4030",
              "INGL4047",
              "INGL4125",
              "INGL4206",
              "ESPA4011"
            ],
            "credits": 18,
            "difficulty_sum": 18
          }
        ],
        "is_complete": false
      },
      {
        "rank": 3,
        "score": 0.05445326278659612,
        "schedule_details": [
          {
            "term_name": "Fall 2026",
            "courses": [
              "MATE4145",
              "FISI3172",
              "CIIC5045",
              "CIIC4030",
              "CIIC4025",
              "CIIC4995",
              "INSO4998",
              "INSO4995",
              "INGL0066",
              "INGL6995",
              "INGL6999",
              "ESPA0041",
              "INGL6996",
              "MATE4050"
            ],
            "credits": 18,
            "difficulty_sum": 25
          },
          {
            "term_name": "Spring 2027",
            "courses": [
              "INME4045",
              "ININ4010",
              "ININ4015",
              "INSO4101",
              "FISI3174",
              "FISI3162",
              "FISI3164"
            ],
            "credits": 18,
            "difficulty_sum": 17
          },
          {
            "term_name": "Fall 2027",
            "courses": [
              "INGE3035",
              "FISI3161",
              "INGE3045",
              "INGE3011",
              "CIIC5110",
              "INSO4117"
            ],
            "credits": 18,
            "difficulty_sum": 13
          },
          {
            "term_name": "Spring 2028",
            "courses": [
              "CIIC5150",
              "INSO4116",
              "INSO4115",
              "CIIC5015",
              "INSO5111",
              "CIIC4998"
            ],
            "credits": 18,
            "difficulty_sum": 18
          },
          {
            "term_name": "Fall 2028",
            "courses": [
              "CIIC5019",
              "CIIC5995",
              "INGL3104",
              "ESPA3102",
              "INGL3101",
              "INGL4000"
            ],
            "credits": 18,
            "difficulty_sum": 13
          },
          {
            "term_name": "Spring 2029",
            "courses": [
              "INGL3205",
              "INGL3191",
              "INGL3225",
              "INGL3227",
              "INGL3231",
              "INGL3236"
            ],
            "credits": 18,
            "difficulty_sum": 12
          },
          {
            "term_name": "Fall 2029",
            "courses": [
              "INGL4255",
              "INGL4028",
              "INGL4075",
              "INGL4205",
              "INGL4208",
              "ESPA4012"
            ],
            "credits": 18,
            "difficulty_sum": 18
          },
          {
            "term_name": "Spring 2030",
            "courses": [
              "INGL4026",
              "INGL4030",
              "INGL4047",
              "INGL4125",
              "INGL4206",
              "ESPA4011"
            ],
            "credits": 18,
            "difficulty_sum": 18
          }
        ],
        "is_complete": false
      }
    ],
    "warnings": [
      "Schedule #1 might be incomplete or exceed target graduation date.",
      "Schedule #2 might be incomplete or exceed target graduation date.",
      "Schedule #3 might be incomplete or exceed target graduation date."
    ]
  };
}

Map<String, dynamic> testRecommendations() {
  return {
    "recommendations": [
      {
        "rank": 1,
        "score": 8,
        "schedule_details": [
          {
            "term_name": "Fall 2026",
            "courses": [
              "ININ4010",
              "INME4045",
              "CIIC4025",
              "INSO4101",
              "MUSI3005",
              "ININ4015"
            ],
            "credits": 18,
            "difficulty_sum": 18
          },
          {
            "term_name": "Spring 2027",
            "courses": [
              "MATE4145",
              "CIIC4050",
              "INEL4115",
              "INGE3011",
              "CIIC4030"
            ],
            "credits": 17,
            "difficulty_sum": 15
          },
          {
            "term_name": "Firstsummer 2027",
            "courses": ["CIIC5045", "INGE3035"],
            "credits": 6,
            "difficulty_sum": 5
          },
          {
            "term_name": "Secondsummer 2027",
            "courses": ["INEL3105", "INGE3045"],
            "credits": 6,
            "difficulty_sum": 4
          },
          {
            "term_name": "Fall 2027",
            "courses": [
              "CIIC4060",
              "CIIC4070",
              "CIIC4995",
              "INSO4995",
              "CIIC5140",
              "INGL3236",
              "INGL3305"
            ],
            "credits": 18,
            "difficulty_sum": 13
          },
          {
            "term_name": "Spring 2028",
            "courses": [
              "ESPA3131",
              "ECON3021",
              "ECON4038",
              "CIIC4151",
              "ALEM3041",
              "CISO4056"
            ],
            "credits": 18,
            "difficulty_sum": 12
          },
          {
            "term_name": "Firstsummer 2028",
            "courses": ["INGE3016", "ADMI4085"],
            "credits": 6,
            "difficulty_sum": 4
          },
          {
            "term_name": "Secondsummer 2028",
            "courses": ["HIST3242", "EDFI3645"],
            "credits": 5,
            "difficulty_sum": 2
          }
        ],
        "is_complete": true
      }
    ],
    "warnings": [
      "Note: 'summer_preference' for 'None' is noted. The current scheduler version primarily includes summer courses based on availability. Advanced summer term management is under development."
    ]
  };
}

Map<String, dynamic> testPreferences() {
  return {
    "program_code": "0508",
    "start_year": 2027,
    "start_term": "Fall",
    "target_grad_year": 2032,
    "target_grad_term": "Spring",
    "taken_courses": [
      "MATE3031",
      "QUIM3131",
      "QUIM3133",
      "CIIC3015",
      "QUIM3132",
      "QUIM3134",
      "CIIC3075",
      "CIIC4010",
      "MATE3032",
      "MATE3063",
      "FISI3171",
      "FISI3173",
      "CIIC4020"
    ],
    "specific_elective_credits_initial": {
      "english": 6,
      "spanish": 6,
      "sociohumanistics": 6,
      "technical": 3,
      "free": 0,
      "kinesiology": 0
    },
    "credit_load_preference": {"min": 9, "max": 18},
    "summer_preference": "None",
    "specific_summers": null,
    "difficulty_curve": "Flat"
  };
}
