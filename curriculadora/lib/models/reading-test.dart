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

Map<String, dynamic> testRecommendations() {
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
