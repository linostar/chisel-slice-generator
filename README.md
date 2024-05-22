# chisel-slice-generator
A generator script for chisel slice definition files.
The script will only output one slice per package, listing all dependencies (package names not slices) and contents under that slice. The output will include a list of dependency package names and a list of file paths for contents. The output will need manual alteration to convert package names to slices, and/or to simplify the path patterns or use Chisel directives if applicable. It can serve as a good basis to create the desired slice definition files.

## How to run
Run:
```
./slice_generator.py <release_number> <arch> <package>
```

For example:
```
./slice_generator.py 24.04 amd64 libcap2
```

The output of the above example command will look like something like the following:
```yaml
package: libcap2
essentials:
  - libcap2_copyright
slices:
  all:
    essentials:
      - libc6
    contents:
      /usr/lib/*-linux-*/libcap.so.2*:
      /usr/lib/*-linux-*/libpsx.so.2*:
  copyright:
    contents:
      /usr/share/doc/libcap2/copyright:
```

After running the script, you need to apply few manual changes to the output:
1. Change the slice name from `all` to something more suitable if needed.
2. Divide the main slice `all` into multiple slices if needed.
3. Replace the packages under `essentials` by their slice couterparts (e.g. `libc6` -> `libc6_libs`).

## Implemented features
- [x] Dependency generation
- [x] Content generation
- [ ] Support for maintainer scripts
- [ ] Recognition of arch-specific dependencies
- [x] Simplification of contents list using glob patterns
- [ ] Usage of arch-agnostic paths in contents list
- [ ] Support for chisel directives
- [x] Support for copyright slices
