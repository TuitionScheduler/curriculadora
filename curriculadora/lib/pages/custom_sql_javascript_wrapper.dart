@JS()
library sqljs;

import 'dart:typed_data';
import 'dart:js_interop';

@JS('initSqlJs')
external dynamic initSqlJs([dynamic config]);

@JS()
@anonymous
class SqlJs {
  external SqlJsDatabase Database(Uint8List buffer);
}

@JS()
@anonymous
class SqlJsDatabase {
  external List<dynamic> exec(String sql);
  external void close();
}