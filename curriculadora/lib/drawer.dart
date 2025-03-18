import 'package:curriculadora/models/curriculadora_cubit.dart';
import 'package:curriculadora/models/curriculadora_pages.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class AppDrawer extends StatefulWidget {
  const AppDrawer({super.key});

  @override
  AppDrawerState createState() => AppDrawerState();
}

class AppDrawerState extends State<AppDrawer> {
  @override
  Widget build(BuildContext context) => Drawer(
          child: ListView(
        padding: EdgeInsets.zero,
        children: [
          const DrawerHeader(
            child: Text('Curriculadora'),
          ),
          ListTile(
            title: const Text('Update Progress'),
            onTap: () {
              Navigator.pop(context);
              BlocProvider.of<CurriculadoraCubit>(context)
                  .setPage(CurriculadoraPage.updateProgress);
            },
          ),
          ListTile(
            title: const Text('Saved Sequences'),
            onTap: () {
              Navigator.pop(context);
              BlocProvider.of<CurriculadoraCubit>(context)
                  .setPage(CurriculadoraPage.viewSequence);
            },
          ),
          ListTile(
            title: const Text('Generate Sequences'),
            onTap: () {
              Navigator.pop(context);
              BlocProvider.of<CurriculadoraCubit>(context)
                  .setPage(CurriculadoraPage.generateSequence);
            },
          ),
          const Divider(),
          ListTile(
            title: const Text('Settings'),
            onTap: () {},
          ),
        ],
      ));
}
