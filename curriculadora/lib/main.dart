import 'package:curriculadora/curriculadora.dart';
import 'package:curriculadora/models/curriculadora_cubit.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: BlocProvider(
        create: (context) => CurriculadoraCubit(),
        child: Curriculadora(),
      ),
    );
  }
}
