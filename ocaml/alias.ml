(* Copyright (C) 2013, Thomas Leonard
 * See the README file for details, or visit http://0install.net.
 *)

open Support.Common
open Options

let handle options flags args =
  match args with
  | [name] -> raise_safe "ERROR: '0alias' has been removed; use '0install update' instead:\n0install update alias:%s" name
  | [name; iface] ->
      Format.fprintf options.stdout "(\"0alias\" is deprecated; using \"0install add\" instead)@.";
      Add.handle options flags [name; iface]
  | _ -> raise_safe "ERROR: '0alias' has been removed; use '0install add' instead"
