import 'package:curriculadora/models/curriculadora_pages.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class CurriculadoraCubit extends Cubit<CurriculadoraState> {
  CurriculadoraCubit()
      : super(CurriculadoraState(page: CurriculadoraPage.viewSequence));

  void setPage(CurriculadoraPage page) {
    emit(state.update(page: page));
  }
}

class CurriculadoraState {
  final CurriculadoraPage page;

  CurriculadoraState({required this.page});

  CurriculadoraState update({
    CurriculadoraPage? page,
  }) {
    return CurriculadoraState(page: page ?? this.page);
  }
}
