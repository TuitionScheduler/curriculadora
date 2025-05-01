// Not a usable file yet

// import 'dart:js_interop_unsafe';

// data_extraction.dart

import 'package:flutter/material.dart';
import 'package:url_launcher/link.dart';
// ------------- For .db file management, storage and queries ------------------
import 'dart:async';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:js_interop';
// import 'package:web/helpers.dart';
// import 'package:indexed_db/indexed_db.dart' as idb;
import 'package:flutter/foundation.dart';
// Cannot import 'io' package because 'io' doesn't exist for web platforms
import 'Platform_Checker/platform_is.dart';
// import 'mobile_data_extraction.dart' as mobile_app;
// import 'web_data_extraction.dart' as web_platform;

// // Conditional imports for mobile vs. web
// export 'mobile_data_extraction.dart'
//   if (dart.library.html) 'web_data_extraction.dart';

import 'data_extraction_wrapper.dart' as wrapper;



// Queries the database for all the data records within a specified table (with all their fields (columns))
Future<List<Map<String, dynamic>>> getAllRecordsFromDBColumn(String tableName, String columnName) async {
  print('Getting all records from $tableName table...');
  // if (kIsWeb){
  //   print('Identified web platform');
  //   result = await getAllRecordsFromDBWeb(tableName);
  //   print('Web Query Result is of type ${result.runtimeType}');
  // }
  // else if (PlatformIs.android || PlatformIs.iOS) {
  //   print('Identified mobile device');
  //   result = await getAllRecordsFromDBMobile(tableName);
  //   print('Mobile Query Result is of type ${result.runtimeType}');
  // }

  String backendAppUrl = 'https://curriculadora-db-app-c1d0a13ccbf0.herokuapp.com';

  // http.Response response = await http.get(Uri.parse('$backendAppUrl/query?table=tableName&column=columnName'));
  http.Response response = await http.get(Uri.parse('$backendAppUrl/table/$tableName/$columnName'));

  if (response.statusCode == 200) {
    print('Successfully returned HTTP query response!');
  } // else {
  //   throw Exception('Http request failed with status: ${response.statusCode}: ${response.reasonPhrase}');
  // }

  final jsonResponse = response.body;
  if (jsonResponse is Map){
    print('$jsonResponse is a Map');
  }
  else {
    print('$jsonResponse is not a Map');
  }
  // List<dynamic> list = jsonResponse JSArrayToList.toDart();
  List<dynamic> responseList = jsonDecode(jsonResponse);
  List<Map<String, dynamic>> result = responseList
    .map((item) => item as Map<String, dynamic>)
    .toList();
  // List<Map<String, dynamic>> result = responseList as List<Map<String, dynamic>>;
  return result;
  

  // if (result.isNotEmpty) {
  //   print('Successfully retreived query result!');
  //   return result;
  // }
  // else {
  //   // print('Table $tableName not found in courses.db');
  //   throw Exception('Table $tableName not found in courses.db'); 
  // }
}

  


// // Downloads the SQLite .db file from GitHub using its raw url
// Future<Uint8List> downloadDatabaseFromGithub() async {
//   String rawUrl = 'https://raw.githubusercontent.com/TuitionScheduler/curriculadora/curriculum-form/data/database/courses.db';
//   http.Response response = await http.get(Uri.parse(rawUrl));
  
//   if (response.statusCode == 200) {
//     print('Successfully downloaded .db file from Github');
//     return response.bodyBytes; // Return the raw bytes of the .db file
//   } else {
//     throw Exception('Could not download the .db file from Github');
//   }
// }


// // Queries the database for all the data records within a specified table (with all their fields (columns))
// Future<List<Map<String, dynamic>>> getAllRecordsFromDB(String tableName) async {
//   print('Getting all records from $tableName table...');
//   List<Map<String, dynamic>> result = [];
//   if (kIsWeb){
//     print('Identified web platform');
//     result = await getAllRecordsFromDBWeb(tableName);
//     print('Web Query Result is of type ${result.runtimeType}');
//   }
//   else if (PlatformIs.android || PlatformIs.iOS) {
//     print('Identified mobile device');
//     result = await getAllRecordsFromDBMobile(tableName);
//     print('Mobile Query Result is of type ${result.runtimeType}');
//   }

//   if (result.isNotEmpty) {
//     print('Successfully retreived query result!');
//     return result;
//   }
//   else {
//     // print('Table $tableName not found in courses.db');
//     throw Exception('Table $tableName not found in courses.db'); 
//   }
// }


// // Queries the database for all the data records within a specified column 
// Future<List<Map<String, dynamic>>> getAllRecordsFromDBColumn(String tableName, String columnName) async {
//   print('Getting all records from column $columnName in $tableName table...');
//   List<Map<String, dynamic>> result = [];
//   if (kIsWeb){
//     print('Identified web platform');
//     result = await getAllRecordsFromDBColumnWeb(tableName, columnName);
//   }
//   else if (PlatformIs.android || PlatformIs.iOS) {
//     print('Identified mobile device');
//     result = await getAllRecordsFromDBColumnMobile(tableName, columnName);
//   }

//   if (result.isNotEmpty) {
//     print('Successfully retreived query result!');
//     return result;
//   }
//   else {
//     // print('Column $columnName not found in $tableName table');
//     throw Exception('Column $columnName not found in $tableName table'); 
//   }
// }


// // Queries the database for a specific data element 
// Future<List<Map<String, dynamic>>> getDataFromDB(String tableName, String columnName, dynamic data) async {
//   print('Getting $columnName : $data from $tableName table...');
//   List<Map<String, dynamic>> result = [];
//   if (kIsWeb) {
//     print('Identified web platform');
//     result = await getDataFromDBWeb(tableName, columnName, data);
//   }
//   else if (PlatformIs.android || PlatformIs.iOS) {
//     print('Identified mobile device');
//     result = await getDataFromDBMobile(tableName, columnName, data);
//   }

//   if (result.isNotEmpty) {
//     print('Successfully retreived query result!');
//     return result;
//   }
//   else {
//     // print('$columnName : $data not found in $tableName table');
//     throw Exception('$columnName : $data not found in $tableName table'); 
//   }
// }


class DataExtraction extends StatefulWidget {
  const DataExtraction({super.key});

  @override
  State<DataExtraction> createState() => _DataExtractionState();
}

class _DataExtractionState extends State<DataExtraction> {
  @override
  void initState() {
    super.initState();
    // _setupPersistentStorage();
  }


  // Download the database and store it in persistent storage when the app starts
  // Future<void> _setupPersistentStorage() async {
  //   print('Started initial database setup...');
  //   // Check if the device is a web platform (browser) 
  //   // Check if the device is Android or IOS (mobile)
  //   if (PlatformIs.android || PlatformIs.iOS) {
  //     print('Using mobile device');
  //     wrapper.checkIfDatabaseStoredInDeviceStorage();
  //   }    

  //   // if (kIsWeb) {
  //   //   print('Using web platform');
  //   //   checkIfDatabaseStoredInIndexedStorage();
  //   // }
  //   // // Check if the device is Android or IOS (mobile)
  //   // else if (PlatformIs.android || PlatformIs.iOS) {
  //   //   print('Using mobile device');
  //   //   checkIfDatabaseStoredInDeviceStorage();
  //   // }   
  // }

  List<Map<String, dynamic>> _dbResults = [];
  bool _loading = false;

  Future<void> _fetchData() async {
    setState(() {
      _loading = true;
    });

    // Replace with your real function and table name
    List<Map<String, dynamic>> results =
        await getAllRecordsFromDBColumn('courses', 'course_code');

    setState(() {
      _dbResults = results;
      _loading = false;
    });
  }



  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[
          const Text(
            'This is the Data Extraction Page',
          ),
          ElevatedButton(
              onPressed: _fetchData,
              child: Text("Trigger database query")),
          SizedBox(
            height: 10,
          ),          
          // Show loading indicator
          if (_loading) CircularProgressIndicator(),

          // Display results
          if (_dbResults.isNotEmpty)
            Padding(
              padding: const EdgeInsets.all(20.0),
              child: _buildTable(),
            ),
        ],
      ),
    );
  }




  // @override
  // Widget build(BuildContext context) {
  //   return Center(
  //     child: Column(
  //       mainAxisAlignment: MainAxisAlignment.center,
  //       children: <Widget>[
  //         const Text(
  //           'This is the Update Progress - Data Extraction Page',
  //         ),
  //         const Text("(MOCKUP)"),
  //         const Text("Your current plan for the next semester is:\n"
  //             "Year: 2024, Term: Spring\n"
  //             "CIIC4151\n"
  //             "CIPO3011\n"
  //             "EDFU3012\n"
  //             "INME4045\n"
  //             "PSIC3002"),
  //         Link(
  //             uri: Uri.parse(
  //                 'https://matrical.site/?term=Spring&year=2024&courses=CIIC4151%2CCIPO3011%2CEDFU3012%2CINME4045%2CPSIC3002'), // hard-coded url
  //             target: LinkTarget.blank,
  //             builder: (context, followLink) => ElevatedButton(
  //                 onPressed: followLink,
  //                 child: const Text("Export to Matrical"))),
  //         const Divider(),
  //         Text("Is this still your plan?"),
  //         ElevatedButton(
  //             onPressed: _fetchData,
  //             child: Text("Yes, continue with this semester")),
  //         SizedBox(
  //           height: 10,
  //         ),
  //         ElevatedButton(
  //             onPressed: () {}, child: Text("No, generate new sequence")),
          
  //         // Show loading indicator
  //         if (_loading) CircularProgressIndicator(),

  //         // Display results
  //         if (_dbResults.isNotEmpty)
  //           Padding(
  //             padding: const EdgeInsets.all(20.0),
  //             child: _buildTable(),
  //           ),
  //       ],
  //     ),
  //   );
  // }

  Widget _buildTable() {
    final columns = _dbResults.first.keys.toList();

    return DataTable(
      columns: columns.map((col) => DataColumn(label: Text(col))).toList(),
      rows: _dbResults
          .map(
            (row) => DataRow(
              cells: columns
                  .map((col) => DataCell(Text(row[col].toString())))
                  .toList(),
            ),
          )
          .toList(),
    );
  }
}
