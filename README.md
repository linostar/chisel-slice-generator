# chisel-slice-checker
A checker script for chisel slice definition files.
This will currently output only one slice per package, listing all dependencies (package names not slices) and contents under that slice. The output is kind of raw and doesn't include glob optimized file naming yet, but it can serve as a good basis to create the desired slice definition files.

## How to run
Run:
```
./slice_checker.py <release_number> <arch> <package>
```

For example:
```
./slice_checker.py 24.04 amd64 libcap2
```

The output of the above example command will look like something like the following:
```yaml
package: libcap2
slices:
  all:
    essentials:
      - libc6
    contents:
      /usr/lib/x86_64-linux-gnu/libcap.so.2:
      /usr/lib/x86_64-linux-gnu/libcap.so.2.66:
      /usr/lib/x86_64-linux-gnu/libpsx.so.2:
      /usr/lib/x86_64-linux-gnu/libpsx.so.2.66:
      /usr/share/doc/libcap2/copyright:
```
