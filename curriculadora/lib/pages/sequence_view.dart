import 'package:curriculadora/models/curriculadora_cubit.dart';
import 'package:curriculadora/models/curriculadora_pages.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class ViewSequence extends StatefulWidget {
  const ViewSequence({super.key});

  @override
  State<ViewSequence> createState() => _ViewSequenceState();
}

class _ViewSequenceState extends State<ViewSequence> {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[
          const Text(
            'You have no saved sequences',
          ),
          TextButton(
              onPressed: () {
                ;
                BlocProvider.of<CurriculadoraCubit>(context)
                    .setPage(CurriculadoraPage.generateSequence);
              },
              child: const Text("+ Generate new sequence"))
        ],
      ),
    );
  }
}
