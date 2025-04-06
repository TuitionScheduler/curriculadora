// Not a usable file yet

import 'package:flutter/material.dart';
import 'package:url_launcher/link.dart';

// Packages for extracting data from Github 
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart'; 
import 'dart:io';
// import 'dart:async';
import 'package:sqflite/sqflite.dart';

downloadDatabaseFromGithub() {
  String rawUrl = 'https://raw.githubusercontent.com/TuitionScheduler/curriculadora/curriculum-form/data/database/courses.db'
  dbUri = await http.get(Uri.parse(rawUrl));
  String dbFilePath = '${Directory.current.path}/frontend_courses.db';
  dbFile = File(dbFilePath);
  await dbFile.writeAsBytes(dbUri.bodyBytes);

  return dbFile;
}

// Perform query
extractDataFromDatabase() {
  File dbFile = await downloadDatabaseFromGithub();
  String dbPath = dbFile.path;
  Database database = await openDatabase(dbPath);
  List<Map<String, dynamic>> result = await database.rawQuery
  ('SELECT * FROM users');
  for (var row in result) {
    print(row); 
  }
  await database.close();
}











import 'dart:async';
import 'package:http/http.dart' as http;
import 'dart:typed_data';
import 'package:indexed_db/indexed_db.dart';
import 'package:sqflite_common_ffi/sqflite_ffi_web.dart';
import 'package:flutter/foundation.dart';

// Downloads the SQLite .db file from GitHub using its raw url
Future<Uint8List> downloadDatabaseFromGithub() async {
  String rawUrl = 'https://raw.githubusercontent.com/TuitionScheduler/curriculadora/curriculum-form/data/database/courses.db'
  http_response = await http.get(Uri.parse(rawUrl));
  
  if (http_response.statusCode == 200) {
    return http_response.bodyBytes; // Return the raw bytes of the .db file
  } else {
    throw Exception('Could not download the .db file from Github');
  }
}

// Creates an IndexedDB that stores courses.db 
Future<void> storeDatabaseInIndexedStorage(Uint8List databaseBytes) async {
  // Creates an IndexedDB and a general ObjectStore to store files in
  indexedStorage = await window.indexedDB!.open("User_Indexed_Storage", version: 1, onUpgradeNeeded: (e) {
    temp = e.target.result as IDBDatabase;
    if (!temp.objectStoreNames.contains("local_files")) {
      temp.createObjectStore("local_files");
    }
    indexedStorage = temp
  });

  // Stores the database in the ObjectStore
  store = indexedStorage.transaction("local_files", "readwrite").objectStore("local_files");
  Blob databaseFile = Blob([databaseBytes]);
  await store.put(databaseFile, "courses.db");
  // do i need to close???
}

// Opens database and configures setup for queries
databaseSetup() {
  final indexedStorage = await window.indexedDB.open("User_Indexed_Storage", version: 1);
  final store = indexedStorage.transaction("local_files", "readonly").objectStore("local_files");
  Blob databaseFile = await store.get("courses.db");
  
  // Sets up database factory for SQLite queries
  if (databaseFile != null) {
    final dbFileBytes = await databaseFile.arrayBuffer();
    Uint8List dbFileUint8List = Uint8List.view(dbFileBytes);

    // final fileBytes = await dbFile!.slice(0, dbFile.size).arrayBuffer();
    // final byteData = ByteData.sublistView(fileBytes as Uint8List);
    
    var factory = databaseFactoryFfiWeb;
    var database = await factory.openDatabaseFromBytes(dbFileUint8List);
    return database
  }
  else {
    await database.close();
    throw Exception('No database found in IndexedStorage.');
  }
}

// Future<void> queryDatabase(int course) async {
//     // Query the database
//     // Returns a list of maps of type String, Dynamic
//     var result = await db.rawQuery('SELECT * FROM courses');
//     print('Courses: $result');
    
//     await db.close();
//     else {
//     print('No database found in IndexedDB.');
//   }
// }

// Queries the database for all programs' data records with all their fields (columns)
Future<void> getAllPrograms(database) async {
  if (kIsweb){
    database = databaseSetup()
    List<Map<String, dynamic>> programs = await database.rawQuery('SELECT * FROM programs');
    await database.close();
  }
}








// class UpdateProgress extends StatefulWidget {
//   const UpdateProgress({super.key});

//   @override
//   State<UpdateProgress> createState() => _UpdateProgressState();
// }

// class _UpdateProgressState extends State<UpdateProgress> {
//   @override
//   Widget build(BuildContext context) {
//     return Center(
//       child: Column(
//         mainAxisAlignment: MainAxisAlignment.center,
//         children: <Widget>[
//           const Text(
//             'This is the Update Progress Page',
//           ),
//           const Text("(MOCKUP)"),
//           const Text("Your current plan for the next semester is:\n"
//               "Year: 2024, Term: Spring\n"
//               "CIIC4151\n"
//               "CIPO3011\n"
//               "EDFU3012\n"
//               "INME4045\n"
//               "PSIC3002"),
//           Link(
//               uri: Uri.parse(
//                   'https://matrical.site/?term=Spring&year=2024&courses=CIIC4151%2CCIPO3011%2CEDFU3012%2CINME4045%2CPSIC3002'), // hard-coded url
//               target: LinkTarget.blank,
//               builder: (context, followLink) => ElevatedButton(
//                   onPressed: followLink,
//                   child: const Text("Export to Matrical"))),
//           const Divider(),
//           Text("Is this still your plan?"),
//           ElevatedButton(
//               onPressed: () {},
//               child: Text("Yes, continue with this semester")),
//           SizedBox(
//             height: 10,
//           ),
//           ElevatedButton(
//               onPressed: () {}, child: Text("No, generate new sequence"))
//         ],
//       ),
//     );
//   }
// }
