from __future__ import annotations

import csv
import hashlib
import json
import random
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

RAW_DATA_DIR = BASE_DIR / "raw_data"
HUGGINGFACE_DIR = RAW_DATA_DIR / "huggingface"
GITHUB_DIR = RAW_DATA_DIR / "github"

OUTPUT_FILE = BASE_DIR / "dataset.jsonl"


# ============================================================
# CONFIGURATION
# ============================================================

# Set this higher after you verify the pipeline works.
#
# Each base Q&A creates up to 3 interviewer examples:
#   strong
#   partial
#   weak
#
# Example:
#   5,000 base Q&A -> up to ~15,000 training conversations.
MAX_EXAMPLES_PER_SOURCE = 5000

RANDOM_SEED = 3407

random.seed(RANDOM_SEED)


# ============================================================
# APTIGRAD SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are AptiGrad, an expert adaptive technical interviewer.

Your job is to evaluate a candidate's technical answer and decide what
question should come next.

You must:

1. Evaluate technical correctness.
2. Evaluate depth and completeness.
3. Identify important misconceptions or missing concepts.
4. Adapt the difficulty based on the candidate's answer.
5. Ask exactly one useful follow-up question.
6. Keep the interview conversational and natural.
7. Never invent technical facts.
8. Return ONLY valid JSON.

The JSON schema is:

{
  "score": 0-10,
  "difficulty_change": "INCREASE" | "DECREASE" | "MAINTAIN",
  "next_question": "..."
}

The score is an internal evaluation signal for the backend.
Do not mention that the candidate is being scored unless explicitly asked.
""".strip()


# ============================================================
# DOMAIN DETECTION
# ============================================================

DOMAIN_KEYWORDS = {
    "Java": [
        "java",
        "jvm",
        "jre",
        "garbage collection",
        "garbage collector",
        "hashmap",
        "concurrenthashmap",
        "synchronized",
        "volatile",
        "thread",
        "executorservice",
        "spring",
        "spring boot",
        "bytecode",
    ],
    "Python": [
        "python",
        "pip",
        "django",
        "flask",
        "asyncio",
        "decorator",
        "generator",
        "list comprehension",
        "gil",
        "cpython",
    ],
    "C++": [
        "c++",
        "cpp",
        "stl",
        "template",
        "pointer",
        "reference",
        "raii",
        "smart pointer",
        "virtual function",
        "move semantics",
        "unique_ptr",
        "shared_ptr",
    ],
    "JavaScript/Web": [
        "javascript",
        "typescript",
        "react",
        "node.js",
        "nodejs",
        "dom",
        "browser",
        "event loop",
        "promise",
        "async/await",
        "frontend",
        "css",
        "html",
        "webpack",
    ],
    "SQL/DBMS": [
        "sql",
        "database",
        "dbms",
        "mysql",
        "postgresql",
        "postgres",
        "mongodb",
        "nosql",
        "index",
        "indexing",
        "query",
        "transaction",
        "acid",
        "join",
        "normalization",
    ],
    "Operating Systems": [
        "operating system",
        "process",
        "thread",
        "deadlock",
        "semaphore",
        "mutex",
        "virtual memory",
        "paging",
        "page fault",
        "kernel",
        "cpu scheduling",
        "context switch",
    ],
    "Computer Networks": [
        "network",
        "tcp",
        "udp",
        "http",
        "https",
        "dns",
        "ip address",
        "router",
        "switch",
        "osi",
        "websocket",
        "tls",
        "latency",
    ],
    "Data Structures & Algorithms": [
        "array",
        "linked list",
        "stack",
        "queue",
        "tree",
        "binary tree",
        "binary search",
        "heap",
        "hash table",
        "graph",
        "dfs",
        "bfs",
        "dynamic programming",
        "backtracking",
        "big-o",
        "complexity",
        "algorithm",
        "sorting",
    ],
    "System Design": [
        "system design",
        "microservice",
        "microservices",
        "distributed system",
        "distributed systems",
        "load balancer",
        "cache",
        "caching",
        "kafka",
        "message queue",
        "sharding",
        "replication",
        "scalability",
        "availability",
        "cap theorem",
        "rate limiting",
        "api gateway",
    ],
}


def detect_domain(question: str, answer: str = "") -> str:
    text = f"{question} {answer}".lower()

    scores = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = 0

        for keyword in keywords:
            if keyword.lower() in text:
                score += 1

        scores[domain] = score

    best_domain = max(scores, key=scores.get)

    if scores[best_domain] == 0:
        return "Software Engineering"

    return best_domain


# ============================================================
# DIFFICULTY
# ============================================================

def estimate_difficulty(question: str, answer: str) -> str:
    text = f"{question} {answer}".lower()

    hard_terms = [
        "distributed",
        "concurrency",
        "race condition",
        "deadlock",
        "lock-free",
        "cas",
        "compare-and-swap",
        "garbage collector",
        "jvm internals",
        "memory model",
        "virtual memory",
        "dynamic programming",
        "graph",
        "system design",
        "scalability",
        "sharding",
        "replication",
        "consistency",
        "cap theorem",
        "transaction isolation",
        "query optimization",
        "event loop",
        "microservices",
    ]

    medium_terms = [
        "difference",
        "compare",
        "explain",
        "how does",
        "why",
        "implementation",
        "complexity",
        "index",
        "thread",
        "api",
        "cache",
        "database",
    ]

    hard_score = sum(1 for term in hard_terms if term in text)
    medium_score = sum(1 for term in medium_terms if term in text)

    if hard_score >= 2:
        return "Hard"

    if hard_score == 1 or medium_score >= 2:
        return "Medium"

    return "Easy"


# ============================================================
# FOLLOW-UP QUESTION GENERATION
# ============================================================

def generate_follow_up(
    question: str,
    answer: str,
    domain: str,
    difficulty: str,
    increase: bool = True,
) -> str:

    q = question.lower()
    a = answer.lower()

    # ---------------- Java ----------------

    if domain == "Java":

        if "garbage" in q or "heap" in q:
            if increase:
                return (
                    "Can you explain how generational garbage collection works "
                    "and why objects are moved between young and old generations?"
                )

            return (
                "Let's step back. What is the difference between Java heap memory "
                "and stack memory?"
            )

        if "hashmap" in q or "concurrenthashmap" in q:
            if increase:
                return (
                    "How does ConcurrentHashMap achieve thread safety without "
                    "locking the entire map, and where does CAS fit into that design?"
                )

            return (
                "Let's start with the basics: what is a HashMap and what problem "
                "does it solve?"
            )

        if "thread" in q or "concurrency" in q:
            if increase:
                return (
                    "What is the difference between synchronized, volatile, "
                    "and atomic variables in Java?"
                )

            return (
                "What is the difference between a process and a thread?"
            )

        if "string" in q or "stringbuilder" in q:
            if increase:
                return (
                    "Why is String immutable in Java, and what implications does "
                    "that have for the String pool and thread safety?"
                )

    # ---------------- Python ----------------

    if domain == "Python":

        if "gil" in q:
            if increase:
                return (
                    "How does the GIL affect CPU-bound versus I/O-bound workloads, "
                    "and when would multiprocessing be preferable?"
                )

            return (
                "What is the Python Global Interpreter Lock, in simple terms?"
            )

        if "decorator" in q:
            if increase:
                return (
                    "Can you explain how decorators work internally and how "
                    "closures are involved?"
                )

            return (
                "What is a Python function and how is it different from a class?"
            )

        if "async" in q or "asyncio" in q:
            if increase:
                return (
                    "How does the asyncio event loop schedule coroutines, "
                    "and what happens when a coroutine performs blocking I/O?"
                )

            return (
                "What is the difference between synchronous and asynchronous code?"
            )

    # ---------------- C++ ----------------

    if domain == "C++":

        if "smart pointer" in q or "unique_ptr" in q or "shared_ptr" in q:
            if increase:
                return (
                    "How does reference counting work in shared_ptr, and what "
                    "problem occurs when shared_ptr objects form a reference cycle?"
                )

            return (
                "What is the purpose of a pointer in C++?"
            )

        if "move" in q or "move semantics" in q:
            if increase:
                return (
                    "Can you explain how rvalue references enable move semantics "
                    "and why moving can be cheaper than copying?"
                )

            return (
                "What is the difference between copying an object and moving it?"
            )

    # ---------------- SQL ----------------

    if domain == "SQL/DBMS":

        if "index" in q or "indexing" in q:
            if increase:
                return (
                    "How does a B-tree index reduce the amount of data the database "
                    "must scan, and what are the trade-offs of adding indexes?"
                )

            return (
                "What is a database index and why is it useful?"
            )

        if "join" in q:
            if increase:
                return (
                    "How would the database optimizer choose between different "
                    "join strategies, and what indexes could improve the join?"
                )

            return (
                "Can you explain the difference between INNER JOIN and LEFT JOIN?"
            )

        if "transaction" in q or "acid" in q:
            if increase:
                return (
                    "Can you explain transaction isolation levels and give an "
                    "example of a dirty read or phantom read?"
                )

            return (
                "What is a database transaction?"
            )

    # ---------------- OS ----------------

    if domain == "Operating Systems":

        if "deadlock" in q:
            if increase:
                return (
                    "What are the four necessary conditions for deadlock, and "
                    "how can an operating system prevent or detect deadlocks?"
                )

            return (
                "What is a deadlock in an operating system?"
            )

        if "process" in q or "thread" in q:
            if increase:
                return (
                    "How does a context switch between threads differ from one "
                    "between processes?"
                )

            return (
                "What is the difference between a process and a thread?"
            )

        if "virtual memory" in q or "paging" in q:
            if increase:
                return (
                    "How does a page fault occur, and how does the operating system "
                    "bring the required page into physical memory?"
                )

            return (
                "Why do operating systems use virtual memory?"
            )

    # ---------------- Networks ----------------

    if domain == "Computer Networks":

        if "tcp" in q or "udp" in q:
            if increase:
                return (
                    "How does TCP establish a connection and provide reliable "
                    "delivery compared with UDP?"
                )

            return (
                "What is the main difference between TCP and UDP?"
            )

        if "dns" in q:
            if increase:
                return (
                    "Can you walk through what happens from entering a domain "
                    "name in a browser until the DNS result is returned?"
                )

            return (
                "What problem does DNS solve?"
            )

        if "http" in q or "https" in q:
            if increase:
                return (
                    "What happens at the TLS layer when a client establishes "
                    "an HTTPS connection?"
                )

            return (
                "What is the difference between HTTP and HTTPS?"
            )

    # ---------------- DSA ----------------

    if domain == "Data Structures & Algorithms":

        if "complexity" in q or "big-o" in q:
            if increase:
                return (
                    "Can you compare the time and space complexity of two possible "
                    "solutions and explain why one scales better?"
                )

            return (
                "What does Big-O notation represent?"
            )

        if "dynamic programming" in q:
            if increase:
                return (
                    "How would you identify the state, transition, and base cases "
                    "for a dynamic programming solution?"
                )

            return (
                "What is the difference between recursion and dynamic programming?"
            )

        if "graph" in q:
            if increase:
                return (
                    "When would you choose BFS over DFS, and how would your choice "
                    "change if you needed the shortest path in an unweighted graph?"
                )

            return (
                "What is a graph and how is it represented in memory?"
            )

    # ---------------- System Design ----------------

    if domain == "System Design":

        if "cache" in q or "caching" in q:
            if increase:
                return (
                    "How would you handle cache invalidation and prevent stale data "
                    "from being served in a distributed system?"
                )

            return (
                "What problem does caching solve?"
            )

        if "microservice" in q:
            if increase:
                return (
                    "How would you handle distributed transactions and service "
                    "failures in a microservices architecture?"
                )

            return (
                "What is a microservice and how is it different from a monolith?"
            )

        if "load balancer" in q:
            if increase:
                return (
                    "How would you design health checks and failover for a load "
                    "balancer in a highly available system?"
                )

            return (
                "What is the purpose of a load balancer?"
            )

        if "scal" in q:
            if increase:
                return (
                    "What is the difference between horizontal and vertical scaling, "
                    "and when would you choose each?"
                )

            return (
                "What does it mean for a system to be scalable?"
            )

    # ---------------- Web ----------------

    if domain == "JavaScript/Web":

        if "event loop" in q:
            if increase:
                return (
                    "Can you explain how the microtask queue and macrotask queue "
                    "interact in the JavaScript event loop?"
                )

            return (
                "Why does JavaScript use an event loop?"
            )

        if "promise" in q or "async" in q:
            if increase:
                return (
                    "How are Promise callbacks scheduled relative to synchronous "
                    "code and other asynchronous tasks?"
                )

            return (
                "What is a Promise in JavaScript?"
            )

    # ---------------- Generic ----------------

    if increase:
        return (
            f"Good foundation. Can you explain the main trade-offs, edge cases, "
            f"and production considerations involved in {domain}?"
        )

    return (
        f"Let's build the foundation first. Can you explain the basic concept "
        f"behind this topic in your own words?"
    )


# ============================================================
# CANDIDATE ANSWER GENERATION
# ============================================================

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)

    return str(value).strip()


def first_sentences(text: str, count: int = 2) -> str:
    text = clean_text(text)

    if not text:
        return ""

    sentences = re.split(r"(?<=[.!?])\s+", text)

    result = " ".join(sentences[:count]).strip()

    return result


def create_partial_answer(reference_answer: str) -> str:
    reference_answer = clean_text(reference_answer)

    if len(reference_answer) < 80:
        words = reference_answer.split()

        if len(words) <= 10:
            return reference_answer

        return " ".join(words[: max(10, len(words) // 2)]) + "..."

    result = first_sentences(reference_answer, 1)

    if len(result) < 40:
        words = reference_answer.split()
        result = " ".join(words[: max(15, len(words) // 2)])

    return result


def create_weak_answer(domain: str) -> str:

    weak_answers = {
        "Java": (
            "I think the JVM handles most of this automatically, so there "
            "isn't much difference in how it works internally."
        ),
        "Python": (
            "Python manages this automatically, so I don't think there are "
            "many important implementation details."
        ),
        "C++": (
            "C++ basically handles this automatically. The main thing is "
            "that the code should compile correctly."
        ),
        "SQL/DBMS": (
            "The database handles this automatically. Usually the query will "
            "just become faster when we add more database features."
        ),
        "Operating Systems": (
            "The operating system manages this automatically, so processes "
            "and memory are mostly handled by the OS."
        ),
        "Computer Networks": (
            "The network stack handles this automatically. The main idea is "
            "that data gets sent from one machine to another."
        ),
        "Data Structures & Algorithms": (
            "It depends on the code, but usually the algorithm just processes "
            "the data and the computer handles the details."
        ),
        "System Design": (
            "We can solve this by adding more servers and using a load balancer. "
            "The system should then scale."
        ),
        "JavaScript/Web": (
            "The browser handles most of this automatically, so JavaScript "
            "doesn't need to manage many of the internal details."
        ),
        "Software Engineering": (
            "I think the framework or runtime handles most of this automatically, "
            "so there aren't many important details."
        ),
    }

    return weak_answers.get(
        domain,
        weak_answers["Software Engineering"]
    )


# ============================================================
# JSON / JSONL / CSV LOADERS
# ============================================================

def read_json_file(path: Path) -> List[Any]:

    try:
        with path.open("r", encoding="utf-8-sig") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            # Some datasets wrap records in a key.
            for key in ("data", "train", "examples", "records"):
                if isinstance(data.get(key), list):
                    return data[key]

            return [data]

    except Exception as exc:
        print(f"[WARN] Failed JSON: {path} -> {exc}")
        return []


def read_jsonl_file(path: Path) -> List[Any]:

    rows = []

    try:
        with path.open("r", encoding="utf-8-sig") as f:
            for line_number, line in enumerate(f, 1):

                line = line.strip()

                if not line:
                    continue

                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    print(
                        f"[WARN] Invalid JSON at {path}:{line_number}"
                    )

    except Exception as exc:
        print(f"[WARN] Failed JSONL: {path} -> {exc}")

    return rows


def read_csv_file(path: Path) -> List[Dict[str, Any]]:

    rows = []

    try:
        with path.open(
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:
                rows.append(dict(row))

    except Exception as exc:
        print(f"[WARN] Failed CSV: {path} -> {exc}")

    return rows


def load_data_file(path: Path) -> List[Any]:

    suffix = path.suffix.lower()

    if suffix == ".json":
        return read_json_file(path)

    if suffix == ".jsonl":
        return read_jsonl_file(path)

    if suffix == ".csv":
        return read_csv_file(path)

    return []


# ============================================================
# ROW EXTRACTION
# ============================================================

def extract_question_answer(
    row: Any,
    source_name: str
) -> Tuple[str, str]:

    if not isinstance(row, dict):
        return "", ""

    # --------------------------------------------------------
    # CodeFeedback
    # --------------------------------------------------------

    question = clean_text(
        row.get("query")
        or row.get("question")
        or row.get("prompt")
        or row.get("instruction")
    )

    answer = clean_text(
        row.get("answer")
        or row.get("response")
        or row.get("output")
        or row.get("completion")
    )

    # --------------------------------------------------------
    # SQL Create Context
    # --------------------------------------------------------

    if source_name == "sql-create-context":

        question = clean_text(row.get("question"))
        context = clean_text(row.get("context"))
        answer = clean_text(row.get("answer"))

        if context:
            question = (
                f"{question}\n\n"
                f"Database schema/context:\n{context}"
            )

        return question, answer

    # --------------------------------------------------------
    # Dolly
    # --------------------------------------------------------

    if source_name == "databricks-dolly-15k":

        question = clean_text(row.get("instruction"))
        answer = clean_text(row.get("response"))

        context = clean_text(row.get("context"))

        if context:
            question = (
                f"{question}\n\n"
                f"Context:\n{context}"
            )

        return question, answer

    # --------------------------------------------------------
    # Glaive
    # --------------------------------------------------------

    if source_name == "glaive-code-assistant-v2":

        question = clean_text(row.get("question"))
        answer = clean_text(row.get("answer"))

        return question, answer

    # --------------------------------------------------------
    # CodeFeedback
    # --------------------------------------------------------

    if source_name == "CodeFeedback-Filtered-Instruction":

        question = clean_text(row.get("query"))
        answer = clean_text(row.get("answer"))

        return question, answer

    # --------------------------------------------------------
    # Generic messages format
    # --------------------------------------------------------

    messages = row.get("messages")

    if isinstance(messages, list):

        user_message = ""
        assistant_message = ""

        for message in messages:

            if not isinstance(message, dict):
                continue

            role = str(message.get("role", "")).lower()
            content = clean_text(message.get("content"))

            if role == "user" and not user_message:
                user_message = content

            elif role == "assistant" and not assistant_message:
                assistant_message = content

        if user_message and assistant_message:
            return user_message, assistant_message

    return question, answer


# ============================================================
# GITHUB MARKDOWN PARSER
# ============================================================

def extract_markdown_pairs(path: Path) -> List[Tuple[str, str]]:

    pairs = []

    try:
        text = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )
    except Exception:
        return pairs

    # Split Markdown into blocks.
    blocks = re.split(r"\n\s*\n", text)

    for i, block in enumerate(blocks):

        block = block.strip()

        if not block:
            continue

        lines = block.splitlines()

        first_line = lines[0].strip()

        # Markdown headings that look like interview questions.
        heading_match = re.match(
            r"^#{1,6}\s+(.+)$",
            first_line
        )

        if heading_match:

            question = heading_match.group(1).strip()

            if (
                "?" in question
                or question.lower().startswith(
                    (
                        "what ",
                        "why ",
                        "how ",
                        "when ",
                        "where ",
                        "which ",
                        "explain ",
                        "difference ",
                    )
                )
            ):

                answer_parts = []

                for next_block in blocks[i + 1: i + 3]:

                    cleaned = next_block.strip()

                    if cleaned.startswith("#"):
                        break

                    if cleaned:
                        answer_parts.append(cleaned)

                answer = "\n\n".join(answer_parts).strip()

                if question and answer:
                    pairs.append((question, answer))

    # Also look for standalone question lines.
    for i, line in enumerate(text.splitlines()):

        line = line.strip()

        if not line:
            continue

        if (
            line.endswith("?")
            and 15 <= len(line) <= 500
        ):

            following_lines = []

            for next_line in text.splitlines()[i + 1:i + 10]:

                next_line = next_line.strip()

                if next_line.startswith("#"):
                    break

                if next_line:
                    following_lines.append(next_line)

            answer = " ".join(following_lines).strip()

            if answer:
                pairs.append((line, answer))

    return pairs


# ============================================================
# RECORD GENERATION
# ============================================================

def make_record(
    domain: str,
    difficulty: str,
    question: str,
    candidate_answer: str,
    score: int,
    difficulty_change: str,
    next_question: str,
) -> Dict[str, Any]:

    user_content = (
        f"Domain: {domain}\n"
        f"Current Difficulty: {difficulty}\n"
        f"Question: {question}\n"
        f"Candidate Answer: {candidate_answer}"
    )

    assistant_content = json.dumps(
        {
            "score": score,
            "difficulty_change": difficulty_change,
            "next_question": next_question,
        },
        ensure_ascii=False,
    )

    return {
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_content,
            },
            {
                "role": "assistant",
                "content": assistant_content,
            },
        ]
    }


def generate_records(
    question: str,
    answer: str,
) -> List[Dict[str, Any]]:

    domain = detect_domain(question, answer)
    difficulty = estimate_difficulty(question, answer)

    records = []

    # --------------------------------------------------------
    # 1. STRONG CANDIDATE
    # --------------------------------------------------------

    next_question = generate_follow_up(
        question=question,
        answer=answer,
        domain=domain,
        difficulty=difficulty,
        increase=True,
    )

    records.append(
        make_record(
            domain=domain,
            difficulty=difficulty,
            question=question,
            candidate_answer=answer,
            score=9,
            difficulty_change="INCREASE",
            next_question=next_question,
        )
    )

    # --------------------------------------------------------
    # 2. PARTIAL CANDIDATE
    # --------------------------------------------------------

    partial = create_partial_answer(answer)

    if partial and partial != answer:

        next_question = generate_follow_up(
            question=question,
            answer=partial,
            domain=domain,
            difficulty=difficulty,
            increase=False,
        )

        records.append(
            make_record(
                domain=domain,
                difficulty=difficulty,
                question=question,
                candidate_answer=partial,
                score=6,
                difficulty_change="MAINTAIN",
                next_question=next_question,
            )
        )

    # --------------------------------------------------------
    # 3. WEAK CANDIDATE
    # --------------------------------------------------------

    weak = create_weak_answer(domain)

    next_question = generate_follow_up(
        question=question,
        answer=weak,
        domain=domain,
        difficulty=difficulty,
        increase=False,
    )

    records.append(
        make_record(
            domain=domain,
            difficulty=difficulty,
            question=question,
            candidate_answer=weak,
            score=3,
            difficulty_change="DECREASE",
            next_question=next_question,
        )
    )

    return records


# ============================================================
# DEDUPLICATION
# ============================================================

def record_hash(record: Dict[str, Any]) -> str:

    user_content = record["messages"][1]["content"]

    return hashlib.sha256(
        user_content.strip().lower().encode("utf-8")
    ).hexdigest()


# ============================================================
# PROCESS HUGGING FACE DATASETS
# ============================================================

def process_huggingface() -> List[Dict[str, Any]]:

    print("\n======================================")
    print("PROCESSING HUGGING FACE DATASETS")
    print("======================================")

    records = []

    if not HUGGINGFACE_DIR.exists():

        print(
            f"[WARN] Missing directory: {HUGGINGFACE_DIR}"
        )

        return records

    source_dirs = [
        p for p in HUGGINGFACE_DIR.iterdir()
        if p.is_dir()
    ]

    for source_dir in source_dirs:

        source_name = source_dir.name

        print(f"\nSource: {source_name}")

        files = []

        for extension in (
            "*.json",
            "*.jsonl",
            "*.csv",
        ):
            files.extend(source_dir.rglob(extension))

        if not files:
            print("  No JSON/JSONL/CSV files found.")
            continue

        source_count = 0

        for file_path in files:

            print(f"  Reading: {file_path.name}")

            rows = load_data_file(file_path)

            for row in rows:

                if source_count >= MAX_EXAMPLES_PER_SOURCE:
                    break

                question, answer = extract_question_answer(
                    row,
                    source_name
                )

                question = clean_text(question)
                answer = clean_text(answer)

                if len(question) < 15:
                    continue

                if len(answer) < 20:
                    continue

                generated = generate_records(
                    question,
                    answer
                )

                records.extend(generated)

                source_count += 1

            if source_count >= MAX_EXAMPLES_PER_SOURCE:
                break

        print(
            f"  Base examples processed: {source_count}"
        )

        print(
            f"  Training records generated: "
            f"{source_count * 3}"
        )

    return records


# ============================================================
# PROCESS GITHUB DATA
# ============================================================

def process_github() -> List[Dict[str, Any]]:

    print("\n======================================")
    print("PROCESSING GITHUB REPOSITORIES")
    print("======================================")

    records = []

    if not GITHUB_DIR.exists():

        print(
            f"[WARN] Missing directory: {GITHUB_DIR}"
        )

        return records

    for repo_dir in GITHUB_DIR.iterdir():

        if not repo_dir.is_dir():
            continue

        repo_name = repo_dir.name

        print(f"\nRepository: {repo_name}")

        markdown_files = list(
            repo_dir.rglob("*.md")
        )

        source_count = 0

        for markdown_file in markdown_files:

            if source_count >= MAX_EXAMPLES_PER_SOURCE:
                break

            pairs = extract_markdown_pairs(
                markdown_file
            )

            for question, answer in pairs:

                if source_count >= MAX_EXAMPLES_PER_SOURCE:
                    break

                if len(question) < 15:
                    continue

                if len(answer) < 20:
                    continue

                generated = generate_records(
                    question,
                    answer
                )

                records.extend(generated)

                source_count += 1

        print(
            f"  Base examples processed: {source_count}"
        )

    return records


# ============================================================
# SHUFFLE
# ============================================================

def shuffle_records(
    records: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:

    random.shuffle(records)

    return records


# ============================================================
# SAVE
# ============================================================

def save_jsonl(
    records: List[Dict[str, Any]]
) -> None:

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as f:

        for record in records:

            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                )
                + "\n"
            )


# ============================================================
# VALIDATION
# ============================================================

def validate_records(
    records: List[Dict[str, Any]]
) -> None:

    print("\n======================================")
    print("VALIDATION")
    print("======================================")

    valid = 0
    invalid = 0

    for record in records:

        try:

            messages = record["messages"]

            assert len(messages) == 3

            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"
            assert messages[2]["role"] == "assistant"

            assistant_json = json.loads(
                messages[2]["content"]
            )

            assert 0 <= assistant_json["score"] <= 10

            assert assistant_json[
                "difficulty_change"
            ] in {
                "INCREASE",
                "DECREASE",
                "MAINTAIN",
            }

            assert assistant_json[
                "next_question"
            ].strip()

            valid += 1

        except Exception as exc:

            invalid += 1

            if invalid <= 5:
                print(
                    "[INVALID RECORD]",
                    exc
                )

    print(f"Valid records:   {valid}")
    print(f"Invalid records: {invalid}")


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")
    print("==============================================")
    print("       APTIGRAD DATA PREPARATION")
    print("==============================================")

    print(
        f"\nRaw data directory:\n{RAW_DATA_DIR}"
    )

    all_records = []

    # Hugging Face
    hf_records = process_huggingface()
    all_records.extend(hf_records)

    # GitHub
    github_records = process_github()
    all_records.extend(github_records)

    print("\n======================================")
    print("DEDUPLICATING")
    print("======================================")

    unique = {}

    for record in all_records:

        key = record_hash(record)

        if key not in unique:
            unique[key] = record

    records = list(unique.values())

    print(
        f"Records before deduplication: "
        f"{len(all_records)}"
    )

    print(
        f"Records after deduplication: "
        f"{len(records)}"
    )

    records = shuffle_records(records)

    validate_records(records)

    save_jsonl(records)

    print("\n======================================")
    print("SUCCESS")
    print("======================================")

    print(
        f"\nGenerated dataset:\n{OUTPUT_FILE}"
    )

    print(
        f"Total training records: {len(records)}"
    )

    print("\nNext step:")
    print("python train_aptigrad.py")


if __name__ == "__main__":
    main()
