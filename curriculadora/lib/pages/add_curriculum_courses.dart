import 'dart:convert';

import 'package:curriculadora/models/reading-test.dart';
import 'package:curriculadora/pages/data_extraction.dart';
import 'package:flutter/material.dart';
import 'package:flutter_form_builder/flutter_form_builder.dart';

// class CourseStatus extends StatefulWidget {
//   final String code;
//   const CourseStatus({super.key, required this.code});
//
//   @override
//   State<CourseStatus> createState() => _CourseStatusState();
// }
//
// class _CourseStatusState extends State<CourseStatus> {
//   @override
//   Widget build(BuildContext context) {
//     return FormBuilderRadioGroup(name: widget.code, options: const [
//       FormBuilderFieldOption(value: 'not-complete', child: Text("NO")),
//       FormBuilderFieldOption(value: 'in-progress', child: Text("IP")),
//       FormBuilderFieldOption(value: 'complete', child: Text("OK")),
//     ]);
//   }
// }

class AddCurriculumCourses extends StatefulWidget {
  final int page;
  final Map<String, dynamic> formDataCurriculum;
  final Map<String, dynamic> formDataCourses;

  final Function(int newPage) changePage;
  final Function(Map<String, dynamic> formData) saveFormCourses;
  const AddCurriculumCourses(
      {super.key,
      required this.page,
      required this.formDataCurriculum,
      required this.formDataCourses,
      required this.changePage,
      required this.saveFormCourses});

  @override
  State<AddCurriculumCourses> createState() => _AddCurriculumCoursesState();
}

class _AddCurriculumCoursesState extends State<AddCurriculumCourses> {
  final _formKey = GlobalKey<FormBuilderState>();
  late Map<String, dynamic> formData = {};
  // Map<String, Map<String, dynamic>> courseTree = testCourses();
  Iterable<String> courses = testCourses().keys;
  bool _loading = false;
  List<Map<String, dynamic>> program = [];

  @override
  void initState() {
    super.initState();
    _fetchData();
  }

  Future<void> _fetchData() async {
    setState(() {
      _loading = true;
    });

    List<Map<String, dynamic>> results = [];

    try {
      results = await getRecord(
          'programs', 'code', widget.formDataCurriculum['program0']);
    } catch (e) {
      print('Query was unable to get record(s) from database: \n $e');
    }

    setState(() {
      program = results;
      // print(program.toString());
      // print(program.length);
      print(courses.toString());
      _loading = false;
    });
  }

  Widget courseStatus(String code) {
    return FormBuilderRadioGroup(
        name: code,
        initialValue: 'not-complete',
        options: const [
          FormBuilderFieldOption(value: 'not-complete', child: Text("NO")),
          FormBuilderFieldOption(value: 'in-progress', child: Text("IP")),
          FormBuilderFieldOption(value: 'complete', child: Text("OK")),
        ]);
  }

  Widget courseStatusForm(List<Map<String, dynamic>> program) {
    Map<String, dynamic> coursesMap = jsonDecode(program[0]['courses']);
    Iterable<String> courses = coursesMap.keys;
    List<Widget> courseList = [];
    for (final course in courses) {
      courseList.add(Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Expanded(child: Text(course.toString())),
          const Spacer(),
          Expanded(child: courseStatus(course)),
        ],
      ));
      courseList.add(const Divider());
    }
    if (program[0]['english'] != 0) {
      int credits = program[0]['english'];
      courseList.add(Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Expanded(child: Text('English credits')),
          Expanded(
              child: FormBuilderSlider(
            name: 'english',
            initialValue: 0,
            min: 0,
            max: credits.toDouble(),
            divisions: credits,
          )),
        ],
      ));
      courseList.add(const Divider());
    }
    if (program[0]['spanish'] != 0) {
      int credits = program[0]['spanish'];
      courseList.add(Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Expanded(child: Text('Spanish credits')),
          Expanded(
              child: FormBuilderSlider(
            name: 'spanish',
            initialValue: 0,
            min: 0,
            max: credits.toDouble(),
            divisions: credits,
          )),
        ],
      ));
      courseList.add(const Divider());
    }
    if (program[0]['humanities'] != 0) {
      int credits = program[0]['humanities'];
      courseList.add(Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Expanded(child: Text('Humanities credits')),
          Expanded(
              child: FormBuilderSlider(
            name: 'humanities',
            initialValue: 0,
            min: 0,
            max: credits.toDouble(),
            divisions: credits,
          )),
        ],
      ));
      courseList.add(const Divider());
    }
    if (program[0]['social'] != 0) {
      int credits = program[0]['social'];
      courseList.add(Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Expanded(child: Text('Social credits')),
          Expanded(
              child: FormBuilderSlider(
            name: 'social',
            initialValue: 0,
            min: 0,
            max: credits.toDouble(),
            divisions: credits,
          )),
        ],
      ));
      courseList.add(const Divider());
    }
    if (program[0]['sociohumanistics'] != 0) {
      int credits = program[0]['sociohumanistics'];
      courseList.add(Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Expanded(child: Text('Sociohumanistic credits')),
          Expanded(
              child: FormBuilderSlider(
            name: 'sociohumanistics',
            initialValue: 0,
            min: 0,
            max: credits.toDouble(),
            divisions: credits,
          )),
        ],
      ));
      courseList.add(const Divider());
    }
    if (program[0]['technical'] != 0) {
      int credits = program[0]['technical'];
      courseList.add(Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Expanded(child: Text('Technical credits')),
          Expanded(
              child: FormBuilderSlider(
            name: 'technical',
            initialValue: 0,
            min: 0,
            max: credits.toDouble(),
            divisions: credits,
          )),
        ],
      ));
      courseList.add(const Divider());
    }
    if (program[0]['free'] != 0) {
      int credits = program[0]['free'];
      courseList.add(Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Expanded(child: Text('Free credits')),
          Expanded(
              child: FormBuilderSlider(
            name: 'free',
            initialValue: 0,
            min: 0,
            max: credits.toDouble(),
            divisions: credits,
          )),
        ],
      ));
      courseList.add(const Divider());
    }
    if (program[0]['kinesiology'] != 0) {
      int credits = program[0]['kinesiology'];
      courseList.add(Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Expanded(child: Text('Kinesiology credits')),
          Expanded(
              child: FormBuilderSlider(
            name: 'kinesiology',
            initialValue: 0,
            min: 0,
            max: credits.toDouble(),
            divisions: credits,
          )),
        ],
      ));
      courseList.add(const Divider());
    }

    courseList.removeLast();
    return Container(
        child: Padding(
      padding: EdgeInsets.all(10),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.start,
        children: courseList,
      ),
    ));
  }

  @override
  Widget build(BuildContext context) {
    if (_loading == true) {
      return const CircularProgressIndicator();
    } else {
      return FormBuilder(
          key: _formKey,
          autovalidateMode: AutovalidateMode.onUnfocus,
          child: SingleChildScrollView(
              child: Column(
            mainAxisAlignment: MainAxisAlignment.start,
            children: <Widget>[
              // courseStatusForm(courses),
              courseStatusForm(program),

              ElevatedButton(
                  onPressed: () {
                    _formKey.currentState?.save();
                    formData = _formKey.currentState!.value;
                    ScaffoldMessenger.of(context).removeCurrentSnackBar();
                    ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text(formData.toString())));
                  },
                  child: const Text("Save")),
              ElevatedButton(
                  onPressed: () {
                    _formKey.currentState?.save();
                    formData = _formKey.currentState!.value;
                    widget.saveFormCourses(formData);
                    widget.changePage(0);
                  },
                  child: Text("Prev")),
              ElevatedButton(
                  onPressed: () {
                    _formKey.currentState?.save();
                    formData = _formKey.currentState!.value;
                    widget.saveFormCourses(formData);
                    widget.changePage(2);
                  },
                  child: Text("Next"))
            ],
          )));
    }
  }
}
