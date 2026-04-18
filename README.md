# draw_zone_tree.py

A Python script that generates a visual tree diagram of the DNS nodes
(unique owner names) in a DNS zone file, annotated with the Resource
Record types present at each node, using Graphviz.

## Prerequisites

- Python 3.6+
- Graphviz system binaries (`brew install graphviz` on macOS)
- Python `graphviz` package (`pip install graphviz`)

## Usage

```
./draw_zone_tree.py <zonefile> <origin> [-o OUTPUT] [-f FORMAT]
```

### Positional arguments

| Argument   | Description                              |
|------------|------------------------------------------|
| `zonefile` | Path to the DNS zone file                |
| `origin`   | Zone origin domain name (e.g. example.com) |

### Optional arguments

| Argument              | Description                          | Default    |
|-----------------------|--------------------------------------|------------|
| `-o`, `--output`      | Output filename (extension optional) | `dns_tree` |
| `-f`, `--format`      | Output format: `png`, `svg`, `pdf`   | `png`      |
| `-h`, `--help`        | Show help message                    |            |

## Examples

Generate a PNG (default):

```
./draw_zone_tree.py zonefile.dnskensa.small.txt dnskensa.com
```

Specify output filename and format:

```
./draw_zone_tree.py zonefile.dnskensa.small.txt dnskensa.com -o my_tree -f svg
```

If the output filename already includes a matching extension, it will not
be duplicated:

```
./draw_zone_tree.py zonefile.dnskensa.small.txt dnskensa.com -o my_tree.png
```

## Zone file format

The script parses zone files in standard presentation format. Each resource
record line should have the owner name as the first field, the `IN` class
token, and the RR type. Comment lines starting with `;;` or `;` are ignored.

Example:

```
example.com.        86400  IN  SOA   mname.example.com. hostmaster.example.com. ...
example.com.        86400  IN  NS    ns1.example.com.
ns1.example.com.    86400  IN  A     192.0.2.1
*.wild.example.com. 86400  IN  A     198.51.100.1
```

## Node types and visual styles

The diagram classifies each node in the zone tree and renders it with a
distinct visual style:

| Node Type          | Color       | Border Style | Description                                       |
|--------------------|-------------|--------------|---------------------------------------------------|
| Zone Apex          | Blue        | Bold solid   | The zone origin with its RR types (SOA, NS, etc.) |
| Normal Node        | Light blue  | Solid        | A standard node with one or more RR types          |
| Empty Non-Terminal | Yellow      | Dashed       | A node with no records, implied by deeper names    |
| Wildcard           | Pink        | Solid        | A wildcard owner name (`*`)                        |
| Delegation Point   | Green       | Bold solid   | A child zone delegation (has NS records)           |
| Glue Record        | Gray        | Dotted       | Address records for delegated nameservers          |

Each node label shows the short (leftmost) name and the set of RR types
present at that node.

## Sample output

Using the included `zonefile.dnskensa.small.txt`:

```
./draw_zone_tree.py zonefile.dnskensa.small.txt dnskensa.com -o dns_tree
```

This produces `dns_tree.png` with a top-down tree rooted at the zone apex,
with edges fanning out diagonally from parent to child nodes.
