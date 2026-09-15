export interface DomainOption {
  id: string;
  label: string;
  blurb: string;
}

export const DOMAINS: DomainOption[] = [
  { id: "JAVA", label: "Java", blurb: "JVM memory architecture, multithreading, OOP, collection framework" },
  { id: "PYTHON", label: "Python", blurb: "GIL, dynamic typing, generators, memory management, decorators" },
  { id: "C", label: "C", blurb: "Pointers, manual memory allocation, structs, low-level execution" },
  { id: "C++", label: "C++", blurb: "RAII, templates, STL, memory management, smart pointers" },
  { id: "JavaScript", label: "JavaScript", blurb: "Event loop, promises, closures, async/await, DOM execution" },
  { id: "DBMS", label: "DBMS", blurb: "Normalization, ACID properties, indexing, SQL queries" },
  { id: "Computer Networks", label: "Computer Networks", blurb: "TCP/IP layers, routing, HTTP/HTTPS, DNS, socket programming" },
  { id: "Operating Systems", label: "Operating Systems", blurb: "Processes, threads, memory paging, deadlocks, CPU scheduling" },
  { id: "DSA", label: "DSA", blurb: "Data structures, algorithms, complexity, dynamic programming" },
];

// Short two-letter tags used on the landing page's domain cards.
export const DOMAIN_ABBR: Record<string, string> = {
  JAVA: "JV",
  PYTHON: "PY",
  C: "C",
  "C++": "CP",
  JavaScript: "JS",
  DBMS: "DB",
  "Computer Networks": "CN",
  "Operating Systems": "OS",
  DSA: "DS",
};