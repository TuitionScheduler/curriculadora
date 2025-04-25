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
