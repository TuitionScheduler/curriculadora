import 'package:curriculadora/drawer.dart';
import 'package:curriculadora/models/curriculadora_cubit.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class Curriculadora extends StatelessWidget {
  Curriculadora({super.key});
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();
  // Scaffold( key: _scaffoldKey,)
  @override
  Widget build(BuildContext context) {
    return BlocBuilder<CurriculadoraCubit, CurriculadoraState>(
        builder: (context, state) {
      return Scaffold(
        key: _scaffoldKey,
        appBar: AppBar(
          title: Text("Curriculadora"),
        ),
        drawer: AppDrawer(),
        body: state.page.displayPage(context),
      );
    });
  }
}
