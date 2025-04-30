import 'package:curriculadora/pages/add_curriculum.dart';
import 'package:curriculadora/pages/generate_sequence.dart';
import 'package:curriculadora/pages/sequence_view.dart';
import 'package:curriculadora/pages/update_progress.dart';
import 'package:curriculadora/pages/data_extraction.dart';
import 'package:flutter/cupertino.dart';

enum CurriculadoraPage {
  viewSequence,
  generateSequence,
  updateProgress,
  dataExtraction,
  addCurriculum;

  Widget displayPage(BuildContext context) {
    switch (this) {
      case CurriculadoraPage.viewSequence:
        return ViewSequence();
      case CurriculadoraPage.generateSequence:
        return GenerateSequence();
      case CurriculadoraPage.updateProgress:
        return UpdateProgress();
      case CurriculadoraPage.dataExtraction:
        return DataExtraction();
      case CurriculadoraPage.addCurriculum:
        return AddCurriculum();
    }
  }
}
