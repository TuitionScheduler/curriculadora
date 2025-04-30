import 'package:curriculadora/models/reading-test.dart';
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
  final Map<String, dynamic> formData;
  final Function(int newPage) changePage;
  final Function(Map<String, dynamic> formData) saveFormCourses;
  const AddCurriculumCourses(
      {super.key,
      required this.page,
      required this.formData,
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

  Widget courseStatusForm(Iterable<String> courses) {
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
    return FormBuilder(
        key: _formKey,
        autovalidateMode: AutovalidateMode.onUnfocus,
        child: SingleChildScrollView(
            child: Column(
          mainAxisAlignment: MainAxisAlignment.start,
          children: <Widget>[
            // courseStatusForm(courses),
            courseStatusForm(courses),

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
