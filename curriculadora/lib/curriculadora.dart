import 'package:curriculadora/drawer.dart';
import 'package:curriculadora/models/curriculadora_cubit.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class Curriculadora extends StatelessWidget {
  const Curriculadora({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<CurriculadoraCubit, CurriculadoraState>(
        builder: (context, state) {
      return Scaffold(
        appBar: AppBar(
          title: Text("Curriculadora"),
        ),
        drawer: AppDrawer(),
        body: state.page.displayPage(context),
      );
    });
  }
}
