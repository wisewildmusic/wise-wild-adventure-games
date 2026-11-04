// The same program as main.js, for QuickJS, a small JavaScript engine that tools/build-scriptoria.sh compiles
// with the game into one Linux program, site/scriptoria, which needs nothing installed. QuickJS reads and writes
// through its own "std" module, where Node.js has "node:fs" and process. That's the only difference.
import * as std from "std";

import { answer } from "./answers.js";

try {
  const request = JSON.parse(std.in.readAsString());
  std.out.puts(JSON.stringify(answer(request)));
  std.out.flush();
} catch (error) {
  std.err.puts(`${error.message}\n`);
  std.exit(2);
}
