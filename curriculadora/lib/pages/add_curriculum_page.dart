import 'package:curriculadora/pages/add_curriculum.dart';
import 'package:curriculadora/pages/add_curriculum_courses.dart';
import 'package:curriculadora/pages/add_curriculum_sequences.dart';
import 'package:flutter/material.dart';

class AddCurriculumPage extends StatefulWidget {
  const AddCurriculumPage({super.key});

  @override
  State<AddCurriculumPage> createState() => _AddCurriculumState();
}

class _AddCurriculumState extends State<AddCurriculumPage> {
  int page = 0;
  late Map<String, dynamic> formDataCurriculum = {};
  late Map<String, dynamic> formDataCourses = {};

  void changePage(int newPage) {
    setState(() {
      page = newPage;
    });
  }

  void saveFormCurriculum(Map<String, dynamic> formData) {
    setState(() {
      formDataCurriculum = formData;
    });
  }

  void saveFormCourses(Map<String, dynamic> formData) {
    setState(() {
      formDataCourses = formData;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (page == 0) {
      return AddCurriculum(
          page: page,
          formData: formDataCurriculum,
          changePage: changePage,
          saveFormCurriculum: saveFormCurriculum);
    } else if (page == 1) {
      return AddCurriculumCourses(
          page: page,
          formDataCurriculum: formDataCurriculum,
          formDataCourses: formDataCourses,
          changePage: changePage,
          saveFormCourses: saveFormCourses);
    } else if (page == 2) {
      return AddCurriculumSequences(
          page: page,
          formDataCurriculum: formDataCurriculum,
          formDataCourses: formDataCourses,
          changePage: changePage);
    } else {
      return Text("Something went wrong");
    }
  }
}
