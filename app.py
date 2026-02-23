from flask import Flask, render_template, jsonify, request
import random
import math

app = Flask(__name__)

# ─── Hash Collision Logic ────────────────────────────────────────────

def generate_puzzle(technique, difficulty):
    """Generate a hash table puzzle for the given technique and difficulty."""
    
    config = {
        "easy":   {"table_size": 7,  "num_keys": 4, "max_val": 99},
        "medium": {"table_size": 11, "num_keys": 7, "max_val": 199},
        "hard":   {"table_size": 13, "num_keys": 9, "max_val": 299},
    }[difficulty]
    
    table_size = config["table_size"]
    num_keys   = config["num_keys"]
    max_val    = config["max_val"]

    if technique == "quadratic_probing":
        keys = _generate_quadratic_keys(table_size, num_keys, max_val, difficulty)
    else:
        keys = _generate_collision_keys(table_size, num_keys, max_val, difficulty)

    if technique == "linear_probing":
        return build_linear_probing(keys, table_size)
    elif technique == "quadratic_probing":
        return build_quadratic_probing(keys, table_size)
    elif technique == "double_hashing":
        return build_double_hashing(keys, table_size)
    elif technique == "chaining":
        return build_chaining(keys, table_size)
    else:
        return build_linear_probing(keys, table_size)


def _generate_collision_keys(table_size, num_keys, max_val, difficulty):
    """Generate keys with forced collisions for linear/double/chaining."""
    keys = []
    used = set()

    # How many collision clusters to force
    clusters = {"easy": 1, "medium": 2, "hard": 3}[difficulty]
    cluster_size = {"easy": 2, "medium": 2, "hard": 3}[difficulty]

    for _ in range(clusters):
        base_hash = random.randint(0, table_size - 1)
        for j in range(cluster_size):
            # Keys that all hash to base_hash: k = base_hash + j*table_size
            k = base_hash + j * table_size
            if 1 <= k <= max_val and k not in used:
                keys.append(k)
                used.add(k)

    # Fill remaining with random non-duplicate keys
    attempts = 0
    while len(keys) < num_keys and attempts < 1000:
        k = random.randint(1, max_val)
        if k not in used:
            keys.append(k)
            used.add(k)
        attempts += 1

    random.shuffle(keys)
    return keys[:num_keys]


def _generate_quadratic_keys(table_size, num_keys, max_val, difficulty):
    """
    Generate keys that cause deep quadratic probe chains.
    Strategy: pick 3-4 keys that all share the same h0 = k % table_size,
    forcing probes at i=1 (offset 1), i=2 (offset 4), i=3 (offset 9)...
    Also mix in a second collision cluster so not all keys land in one spot.
    """
    keys = []
    used = set()

    # Cluster sizes by difficulty: force deeper probe chains
    cluster_configs = {
        "easy":   [(1, 3)],           # 1 cluster of 3 → probes up to i=2
        "medium": [(1, 4), (1, 2)],   # cluster of 4 + cluster of 2 → probes up to i=3
        "hard":   [(1, 4), (1, 3)],   # cluster of 4 + cluster of 3 → probes up to i=3/i=2
    }[difficulty]

    for (_, size) in cluster_configs:
        base_hash = random.randint(1, table_size - 2)
        for j in range(size):
            # All these keys share the same initial hash = base_hash
            k = base_hash + j * table_size
            if 1 <= k <= max_val and k not in used:
                keys.append(k)
                used.add(k)

    # Fill remainder with randoms
    attempts = 0
    while len(keys) < num_keys and attempts < 1000:
        k = random.randint(1, max_val)
        if k not in used:
            keys.append(k)
            used.add(k)
        attempts += 1

    random.shuffle(keys)
    return keys[:num_keys]


def build_linear_probing(keys, table_size):
    table = [None] * table_size
    steps = []
    
    for key in keys:
        h = key % table_size
        original_h = h
        probe = 0
        placed = False
        probe_seq = [h]
        
        while probe < table_size:
            if table[h] is None:
                table[h] = key
                # Hint: show the formula expression but NOT the resolved slot number
                if probe == 0:
                    hint = f"h({key}) = {key} mod {table_size} = ?"
                else:
                    hint = f"h({key}) = {key} mod {table_size} = {original_h} → collision(s), probe i=1..{probe}"
                steps.append({
                    "key": key,
                    "initial_hash": original_h,
                    "probe_sequence": probe_seq,
                    "final_index": h,
                    "collisions": probe,
                    "formula": hint
                })
                placed = True
                break
            probe += 1
            h = (original_h + probe) % table_size
            probe_seq.append(h)
        
        if not placed:
            steps.append({"key": key, "error": "Table full"})
    
    return {
        "technique": "linear_probing",
        "technique_label": "Linear Probing",
        "table_size": table_size,
        "keys": keys,
        "solution": table,
        "steps": steps,
        "description": "On collision, probe next slot: h(k, i) = (h(k) + i) mod m",
        "formula_label": "h(k, i) = (k mod m + i) mod m"
    }


def build_quadratic_probing(keys, table_size):
    table = [None] * table_size
    steps = []
    
    for key in keys:
        h0 = key % table_size
        placed = False
        probe_seq = [h0]
        
        for i in range(table_size):
            h = (h0 + i*i) % table_size
            if i > 0:
                probe_seq.append(h)
            if table[h] is None:
                table[h] = key
                # Show the formula with the i² expansion but leave final slot blank
                if i == 0:
                    hint = f"h({key}) = {key} mod {table_size} = ?"
                else:
                    # Show each probe step as an unsolved expression
                    probe_exprs = []
                    for p in range(i + 1):
                        probe_exprs.append(f"i={p}: ({h0} + {p}²) mod {table_size} = ?")
                    hint = " | ".join(probe_exprs)
                steps.append({
                    "key": key,
                    "initial_hash": h0,
                    "probe_sequence": probe_seq[:i+1],
                    "final_index": h,
                    "collisions": i,
                    "formula": hint
                })
                placed = True
                break
        
        if not placed:
            steps.append({"key": key, "error": "No slot found (quadratic probing exhausted)"})
    
    return {
        "technique": "quadratic_probing",
        "technique_label": "Quadratic Probing",
        "table_size": table_size,
        "keys": keys,
        "solution": table,
        "steps": steps,
        "description": "On collision, probe with quadratic increments: h(k, i) = (h(k) + i²) mod m",
        "formula_label": "h(k, i) = (k mod m + i²) mod m"
    }


def build_double_hashing(keys, table_size):
    table = [None] * table_size
    steps = []
    
    # h2 must never be 0, use: h2(k) = 1 + (k mod (m-1))
    def h2(k):
        return 1 + (k % (table_size - 1))
    
    for key in keys:
        h0 = key % table_size
        step2 = h2(key)
        placed = False
        probe_seq = [h0]
        
        for i in range(table_size):
            h = (h0 + i * step2) % table_size
            if i > 0:
                probe_seq.append(h)
            if table[h] is None:
                # Show both hash function expressions unsolved
                if i == 0:
                    hint = f"h1({key}) = {key} mod {table_size} = ? | h2({key}) = 1 + ({key} mod {table_size-1}) = ?"
                else:
                    hint = (f"h1({key}) = {key} mod {table_size} = {h0} | "
                            f"h2({key}) = 1 + ({key} mod {table_size-1}) = {step2} | "
                            f"collision(s) → i={i}: ({h0} + {i}×{step2}) mod {table_size} = ?")
                steps.append({
                    "key": key,
                    "initial_hash": h0,
                    "h2_value": step2,
                    "probe_sequence": probe_seq[:i+1],
                    "final_index": h,
                    "collisions": i,
                    "formula": hint
                })
                placed = True
                break
        
        if not placed:
            steps.append({"key": key, "error": "Table full"})
    
    return {
        "technique": "double_hashing",
        "technique_label": "Double Hashing",
        "table_size": table_size,
        "keys": keys,
        "solution": table,
        "steps": steps,
        "description": "On collision, use second hash function: h(k,i) = (h1(k) + i·h2(k)) mod m",
        "formula_label": "h(k,i) = (k mod m + i·(1 + k mod (m-1))) mod m"
    }


def build_chaining(keys, table_size):
    table = [[] for _ in range(table_size)]
    steps = []
    
    for key in keys:
        h = key % table_size
        table[h].append(key)
        steps.append({
            "key": key,
            "initial_hash": h,
            "final_index": h,
            "chain_length": len(table[h]),
            "formula": f"{key} % {table_size} = {h}"
        })
    
    # Convert to serializable format
    solution = [list(chain) for chain in table]
    
    return {
        "technique": "chaining",
        "technique_label": "Separate Chaining",
        "table_size": table_size,
        "keys": keys,
        "solution": solution,
        "steps": steps,
        "description": "Each slot holds a linked list. Colliding keys are chained together.",
        "formula_label": "h(k) = k mod m → append to chain at index"
    }


# ─── Routes ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/puzzle")
def get_puzzle():
    technique  = request.args.get("technique", "linear_probing")
    difficulty = request.args.get("difficulty", "easy")
    puzzle = generate_puzzle(technique, difficulty)
    return jsonify(puzzle)

if __name__ == "__main__":
    print("🚀 Hash Collision Visualizer running at http://localhost:5050")
    app.run(debug=True, port=5050)
