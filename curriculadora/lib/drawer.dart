import 'package:flutter/material.dart';

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
              Navigator.pushNamed(context, "/updateProgress");
            },
          ),
          ListTile(
            title: const Text('Saved Sequences'),
            onTap: () {
              Navigator.pop(context);
              Navigator.pushNamed(context, "/");
            },
          ),
          ListTile(
            title: const Text('Generate Sequences'),
            onTap: () {
              Navigator.pop(context);
              Navigator.pushNamed(context, "/generate");
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
