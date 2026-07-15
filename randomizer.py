import pandas as pd
import random
import json
from collections import defaultdict
import csv


# ----------------------------
# SETTINGS
# ----------------------------

# grade pairs to be evaluated are stored here (24 synthetic pairs)
INPUT_CSV = "grade_pairs.csv"

# names are pulled from SSA list with percentage of popularity
INPUT_NAMES_JSON = "names_with_pct.json"

# save to this file for reading
OUTPUT_JSON = "group_assignment.json"

total_groups = 80
groups_per_cluster = 8
num_clusters = 10

# Number of synthetic pairs (real pair appended as pair_id 25)
REAL_PAIR_ID = 25

# establish seed for reproducibility
random.seed(123)

# gender split - how many mixed pairs?
MF_split = .75

# ----------------------------
# GPA MAPPING
# ----------------------------

GRADE_TO_GPA = {
    "A":  4.0,
    "A-": 3.75,
    "B+": 3.25,
    "B":  3.0,
    "B-": 2.75,
    "C+": 2.25,
    "C":  2.0,
    "C-": 1.75,
}

def calc_gpa(grades):
    return round(sum(GRADE_TO_GPA[g] for g in grades) / len(grades), 3)

# ----------------------------
# REAL CANDIDATE PROFILES
# Both share pair_id 25; only one appears per group.
# profile_1 is the better quiz performer
# riley_graham:    Riley outperformed Graham on the quiz
# daniel_samantha: Samantha outperformed Daniel on the quiz
# ----------------------------
REAL_PAIRS = {
    "riley_graham": {
        "profile_1": {
            "name_id":        57395,
            "name":           "Riley",
            "gender":         "F",
            "gpa":            3.5625,
            "grade_1":        "A",
            "grade_2":        "A",
            "grade_4":        "B+",
            "grade_3":        "B",
        },
        "profile_2": {
            "name_id":        93725,
            "name":           "Graham",
            "gender":         "M",
            "gpa":            3.5625,
            "grade_1":        "A",
            "grade_2":        "A",
            "grade_4":        "B+",
            "grade_3":        "B",
        },
    },
    "daniel_samantha": {
        "profile_1": {
            "name_id":        58963,
            "name":           "Samantha",
            "gender":         "F",
            "gpa":            3.9375,
            "grade_1":        "A",
            "grade_2":        "A",
            "grade_3":        "A",
            "grade_4":        "A-",
        },
        "profile_2": {
            "name_id":        94864,
            "name":           "Daniel",
            "gender":         "M",
            "gpa":            3.875,
            "grade_1":        "A",
            "grade_2":        "A",
            "grade_3":        "A-",
            "grade_4":        "A-",
        },
    },
}

# ----------------------------
# READ INPUT FILES
# ----------------------------
df = pd.read_csv(INPUT_CSV)

with open(INPUT_NAMES_JSON, "r", encoding="utf-8") as f:
    names_data = json.load(f)

# ----------------------------
# BUILD NAME POOLS
# ----------------------------
male_names = [x for x in names_data if 1   <= x["id"] <= 50]
female_names = [x for x in names_data if 151 <= x["id"] <= 200]


# sum over total births and then divide to the get the weight (per pool)
def normalize_weights(name_pool, weight_key="births"):
    total = sum(x[weight_key] for x in name_pool)
    return [x[weight_key] / total for x in name_pool]


male_weights = normalize_weights(male_names)
female_weights = normalize_weights(female_names)


# draw names with weighted likelihood
def draw_name(gender, exclude_name=None):
    if gender == "M":
        pool, weights = male_names, male_weights
    elif gender == "F":
        pool, weights = female_names, female_weights
    else:
        raise ValueError("gender must be 'M' or 'F'")

    while True:
        picked = random.choices(pool, weights=weights, k=1)[0]
        if exclude_name is None or picked["name"] != exclude_name:
            return {"name_id": picked["id"], "name": picked["name"], "gender": gender}


# ----------------------------
# BUILD PAIR LOOKUP
# ----------------------------
pair_lookup = {}

for _, row in df.iterrows():
    pair_id = int(row["grade_id"])
    profile_1_original = {str(i): row[f"Grade {i}"]   for i in range(1, 5)}
    profile_2_original = {str(i): row[f"Grade {i}.1"] for i in range(1, 5)}
    pair_lookup[pair_id] = {
        "profile_1": profile_1_original,
        "profile_2": profile_2_original,
        "gpa_1":     calc_gpa(list(profile_1_original.values())),
        "gpa_2":     calc_gpa(list(profile_2_original.values())),
    }

all_pair_ids = sorted(pair_lookup.keys())


# ----------------------------
# GENDER STRUCTURE
# Shuffle the pairs
# Assign the pairs sequentially across 8 groups
# Every 8 groups it reshuffles the random order of pairs
# ----------------------------

def shuffle_to_create_gender_pair_map(all_pair_ids, pair_lookup, total_groups=80, groups_per_cluster=8):
    # each cluster of 8 groups resets the assignment, so with every 8 groups there is an even distribution of gender and
    # pair assignments
    num_clusters = total_groups // groups_per_cluster # always 80 groups, 8 clusters, 10 total clusters

    # corrections change the start point of grade pair assignment so that if group 2 sees pairs x,y,z as MM in stage 1
    # they don't then evaluate the choices of group 1 where pairs x,y,z were FF
    corrections = [0, 3, -3, 0]
    gender_pair_map = {}

    real_pair_keys = list(REAL_PAIRS.keys())  # ["riley_graham", "daniel_samantha"]

    for cluster_index in range(num_clusters):
        group_start = cluster_index * groups_per_cluster
        groups_in_cluster = list(range(group_start, group_start + groups_per_cluster))

        cluster_pair_ids = all_pair_ids.copy()
        random.shuffle(cluster_pair_ids)

        n = len(cluster_pair_ids)

        # see latex writeup for how this assignment works with changing start positions and corrections
        for local_index, group in enumerate(groups_in_cluster):
            correction = corrections[local_index % 4]

            mm_start = (local_index * 3 + correction) % n
            ff_start = (local_index * 3 + 3 + correction) % n
            fm_start = (local_index * 3 + 15 + correction) % n

            mm_positions = {(mm_start + i) % n for i in range(3)}
            ff_positions = {(ff_start + i) % n for i in range(3)}
            fm_positions = {(fm_start + i) % n for i in range(9)}
            mf_positions = set(range(n)) - mm_positions - ff_positions - fm_positions

            assert mm_positions.isdisjoint(ff_positions), f"MM/FF overlap in cluster {cluster_index + 1}, group {local_index + 1}!"
            assert mm_positions.isdisjoint(fm_positions), f"MM/FM overlap in cluster {cluster_index + 1}, group {local_index + 1}!"
            assert ff_positions.isdisjoint(fm_positions), f"FF/FM overlap in cluster {cluster_index + 1}, group {local_index + 1}!"
            assert len(mf_positions) == 9, f"MF should have 9 positions, got {len(mf_positions)} in cluster {cluster_index + 1}, group {local_index + 1}!"

            # --- Real pair assignment ---
            # deterministic alternation: even local_index -> option 0, odd local_index -> option 1
            # groups_per_cluster is even (8), so this also guarantees no repeat across cluster boundaries
            chosen_key = real_pair_keys[local_index % 2]

            real_pair_data = REAL_PAIRS[chosen_key]
            real_pair_entry = {
                "pair_id": 25,
                "real_pair": chosen_key,
                "gender_combo": (real_pair_data["profile_1"]["gender"], real_pair_data["profile_2"]["gender"]),
                "profile_1": real_pair_data["profile_1"],
                "profile_2": real_pair_data["profile_2"],
            }

            # --- Regular pair assignments ---
            assignments = [real_pair_entry]  # real pair goes first
            for i, pair_id in enumerate(cluster_pair_ids):
                pair_data = pair_lookup[pair_id]
                gender = ("M", "M") if i in mm_positions else \
                    ("F", "F") if i in ff_positions else \
                        ("F", "M") if i in fm_positions else \
                            ("M", "F")

                g1, g2 = gender  # unpack the two genders for this pair

                name_1 = draw_name(g1)
                name_2 = draw_name(g2, exclude_name=name_1["name"])  # avoid same name in a pair

                assignments.append({
                    "pair_id": pair_id,
                    "gender_combo": gender,
                    "profile_1": {
                        **name_1,
                        "gpa": pair_data["gpa_1"],
                        "grade_1": pair_data["profile_1"]["1"],
                        "grade_2": pair_data["profile_1"]["2"],
                        "grade_3": pair_data["profile_1"]["3"],
                        "grade_4": pair_data["profile_1"]["4"],
                    },
                    "profile_2": {
                        **name_2,
                        "gpa": pair_data["gpa_2"],
                        "grade_1": pair_data["profile_2"]["1"],
                        "grade_2": pair_data["profile_2"]["2"],
                        "grade_3": pair_data["profile_2"]["3"],
                        "grade_4": pair_data["profile_2"]["4"],
                    },
                })
            gender_pair_map[group] = assignments

    return gender_pair_map


# ----------------------------
# GENERATE JSON
# ----------------------------
output = shuffle_to_create_gender_pair_map(all_pair_ids, pair_lookup, total_groups=80, groups_per_cluster=8)

with open(OUTPUT_JSON, "w") as f:
    json.dump({str(k): v for k, v in output.items()}, f, indent=2)


# ----------------------------
# RANDOMIZATION CHECKS
# The rest of the document produces optional outputs that check the validity of the randomization
# ----------------------------

# # ----------------------------
# # EXPORT NAMES CSV
# # ----------------------------
# import csv
#
# names_rows = []
#
# for entry in output:
#     session_num = entry["session"]
#     for group_entry in entry["groups"]:
#         group_name = group_entry["group"]
#         for pair in group_entry["pair_sequence"]:
#             pair_id = pair["pair_id"]
#             # Real pair profiles don't have randomly drawn names, skip
#             if pair_id == REAL_PAIR_ID:
#                 continue
#             for profile_num, profile_key in [(1, "profile_1"), (2, "profile_2")]:
#                 p = pair[profile_key]
#                 names_rows.append({
#                     "session":      session_num,
#                     "group":        group_name,
#                     "pair_id":      pair_id,
#                     "profile":      profile_num,
#                     "name_id":      p["name_id"],
#                     "name":         p["name"],
#                     "gender":       p["gender"],
#                 })
#
# names_csv_path = "randomization_checks\assigned_names.csv"
# with open(names_csv_path, "w", newline="", encoding="utf-8") as f:
#     writer = csv.DictWriter(f, fieldnames=["session", "group", "pair_id", "profile", "name_id", "name", "gender"])
#     writer.writeheader()
#     writer.writerows(names_rows)
#
# print(f"Names CSV written to {names_csv_path}")
#


# ----------------------------
# EXPORT GENDER SUMMARY CSV
# ----------------------------

gender_summary = defaultdict(lambda: {"F/F": 0, "M/F": 0, "M/M": 0, "F/M": 0})
grade_registry = {}

for group, pairs in output.items():
    for pair in pairs:
        pair_id = pair["pair_id"]
        if pair_id == REAL_PAIR_ID:
            continue
        g1 = pair["profile_1"]["gender"]
        g2 = pair["profile_2"]["gender"]
        key = f"{g1}/{g2}"
        gender_summary[pair_id][key] += 1

        if pair_id not in grade_registry:
            grade_registry[pair_id] = {
                "grade_dict1__1": pair["profile_1"]["grade_1"],
                "grade_dict2__1": pair["profile_1"]["grade_2"],
                "grade_dict3__1": pair["profile_1"]["grade_3"],
                "grade_dict4__1": pair["profile_1"]["grade_4"],
                "grade_dict1__2": pair["profile_2"]["grade_1"],
                "grade_dict2__2": pair["profile_2"]["grade_2"],
                "grade_dict3__2": pair["profile_2"]["grade_3"],
                "grade_dict4__2": pair["profile_2"]["grade_4"],
            }

gender_csv_path = "randomization_checks\gender_summary.csv"
fieldnames = ["pair_id", "grade_dict1__1", "grade_dict2__1", "grade_dict3__1", "grade_dict4__1",
                          "grade_dict1__2", "grade_dict2__2", "grade_dict3__2", "grade_dict4__2",
                          "F/F", "M/F", "M/M", "F/M"]
with open(gender_csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for pair_id in sorted(gender_summary.keys()):
        row = {"pair_id": pair_id, **grade_registry[pair_id], **gender_summary[pair_id]}
        writer.writerow(row)

print(f"Gender summary CSV written to {gender_csv_path}")
# # ----------------------------
# # EXPORT SESSION-GROUP GENDER DISTRIBUTION CSV
# # ----------------------------
# from collections import defaultdict
#
# session_group_gender = defaultdict(lambda: {"M/F": 0, "F/M": 0, "M/M": 0, "F/F": 0})
#
# for entry in output:
#     session_num = entry["session"]
#     for group_entry in entry["groups"]:
#         group_name = group_entry["group"]
#         key = (session_num, group_name)
#         for pair in group_entry["pair_sequence"]:
#             if pair["pair_id"] == REAL_PAIR_ID:
#                 continue
#             g1 = pair["profile_1"]["gender"]
#             g2 = pair["profile_2"]["gender"]
#             combo = f"{g1}/{g2}"
#             session_group_gender[key][combo] += 1
#
# sg_csv_path = "randomization_checks\session_group_gender_dist.csv"
# with open(sg_csv_path, "w", newline="", encoding="utf-8") as f:
#     fieldnames = ["session", "group", "M/F", "F/M", "M/M", "F/F", "total"]
#     writer = csv.DictWriter(f, fieldnames=fieldnames)
#     writer.writeheader()
#     for (session_num, group_name) in sorted(session_group_gender.keys()):
#         counts = session_group_gender[(session_num, group_name)]
#         row = {
#             "session":    session_num,
#             "group":      group_name,
#             "M/F":        counts["M/F"],
#             "F/M":        counts["F/M"],
#             "M/M":        counts["M/M"],
#             "F/F":        counts["F/F"],
#             "total":      sum(counts.values()),
#         }
#         writer.writerow(row)
#
# print(f"Session-group gender distribution written to {sg_csv_path}")
#
# ----------------------------
# EXPORT RANDOMIZATION SUMMARY TXT
# ----------------------------

# ----------------------------
# VERIFICATION CHECKS
# ----------------------------

VALID_GRADES = {"A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"}
REQUIRED_PROFILE_FIELDS = {"name", "name_id", "gender", "gpa", "grade_1", "grade_2", "grade_3", "grade_4"}

errors = []
warnings = []

real_pair_counts = defaultdict(int)          # riley_graham vs daniel_samantha tally
cluster_shuffles = defaultdict(set)          # track pair_id order per cluster

for group in sorted(output.keys()):
    pairs = output[group]
    cluster_index = group // 8

    # --- Structural checks ---
    if len(pairs) != 25:
        errors.append(f"Group {group}: expected 25 pairs, got {len(pairs)}")

    if pairs[0]["pair_id"] != REAL_PAIR_ID:
        errors.append(f"Group {group}: real pair (id={REAL_PAIR_ID}) is not first in list")

    regular_pairs = [p for p in pairs if p["pair_id"] != REAL_PAIR_ID]
    pair_ids_in_group = [p["pair_id"] for p in regular_pairs]

    if sorted(pair_ids_in_group) != sorted(all_pair_ids):
        missing = set(all_pair_ids) - set(pair_ids_in_group)
        dupes = [pid for pid in pair_ids_in_group if pair_ids_in_group.count(pid) > 1]
        if missing:
            errors.append(f"Group {group}: missing pair_ids {missing}")
        if dupes:
            errors.append(f"Group {group}: duplicate pair_ids {set(dupes)}")

    # --- Gender count checks ---
    combo_counts = {"M/F": 0, "F/M": 0, "M/M": 0, "F/F": 0}
    for pair in regular_pairs:
        key = f"{pair['profile_1']['gender']}/{pair['profile_2']['gender']}"
        if key in combo_counts:
            combo_counts[key] += 1
        else:
            errors.append(f"Group {group}, pair {pair['pair_id']}: invalid gender combo '{key}'")

    if combo_counts["M/M"] != 3:
        errors.append(f"Group {group}: expected 3 M/M, got {combo_counts['M/M']}")
    if combo_counts["F/F"] != 3:
        errors.append(f"Group {group}: expected 3 F/F, got {combo_counts['F/F']}")
    if combo_counts["F/M"] != 9:
        errors.append(f"Group {group}: expected 9 F/M, got {combo_counts['F/M']}")
    if combo_counts["M/F"] != 9:
        errors.append(f"Group {group}: expected 9 M/F, got {combo_counts['M/F']}")

    # --- Real pair checks ---
    real_pair = pairs[0]
    real_key = real_pair.get("real_pair", None)
    if real_key is None:
        errors.append(f"Group {group}: real pair missing 'real_pair' key")
    else:
        real_pair_counts[real_key] += 1
        declared_combo = real_pair.get("gender_combo", ())
        actual_combo = (real_pair["profile_1"]["gender"], real_pair["profile_2"]["gender"])
        if tuple(declared_combo) != actual_combo:
            errors.append(f"Group {group}: real pair gender_combo {declared_combo} "
                          f"doesn't match profiles {actual_combo}")

    # --- Even/odd real pair alternation ---
    if group % 2 == 0:
        expected_next = {"riley_graham": "daniel_samantha", "daniel_samantha": "riley_graham"}
        next_group = group + 1
        if next_group in output:
            next_real = next(
                (p.get("real_pair") for p in output[next_group] if p["pair_id"] == REAL_PAIR_ID), None
            )
            if real_key and next_real and next_real != expected_next[real_key]:
                errors.append(f"Groups {group}/{next_group}: real pair alternation broken "
                               f"(even={real_key}, odd={next_real})")

    # --- Profile field and value checks ---
    for pair in pairs:
        pair_id = pair["pair_id"]
        for profile_key in ["profile_1", "profile_2"]:
            p = pair[profile_key]

            # Missing fields
            missing_fields = REQUIRED_PROFILE_FIELDS - set(p.keys())
            if missing_fields:
                errors.append(f"Group {group}, pair {pair_id}, {profile_key}: "
                               f"missing fields {missing_fields}")
                continue  # skip further checks on this profile

            # Valid gender
            if p["gender"] not in ("M", "F"):
                errors.append(f"Group {group}, pair {pair_id}, {profile_key}: "
                               f"invalid gender '{p['gender']}'")

            # Name ID range
            if pair_id != REAL_PAIR_ID:
                if p["gender"] == "M" and not (1 <= p["name_id"] <= 50):
                    errors.append(f"Group {group}, pair {pair_id}, {profile_key}: "
                                  f"male name_id {p['name_id']} out of range 1-50")
                if p["gender"] == "F" and not (151 <= p["name_id"] <= 200):
                    errors.append(f"Group {group}, pair {pair_id}, {profile_key}: "
                                  f"female name_id {p['name_id']} out of range 151-200")

            # Valid grades
            for g in ["grade_1", "grade_2", "grade_3", "grade_4"]:
                if p[g] not in VALID_GRADES:
                    errors.append(f"Group {group}, pair {pair_id}, {profile_key}: "
                                  f"invalid grade '{p[g]}' in {g}")

            # GPA sanity
            if pair_id != REAL_PAIR_ID:
                if p["gpa"] <= 0:
                    errors.append(f"Group {group}, pair {pair_id}, {profile_key}: "
                                  f"GPA {p['gpa']} is zero or negative")
                recalc = calc_gpa([p["grade_1"], p["grade_2"], p["grade_3"], p["grade_4"]])
                if abs(recalc - p["gpa"]) > 0.001:
                    errors.append(f"Group {group}, pair {pair_id}, {profile_key}: "
                                  f"GPA mismatch — stored {p['gpa']}, recalculated {recalc:.4f}")

    # --- Within-pair name uniqueness ---
    for pair in regular_pairs:
        n1 = pair["profile_1"]["name"]
        n2 = pair["profile_2"]["name"]
        if n1 == n2:
            errors.append(f"Group {group}, pair {pair['pair_id']}: "
                          f"both profiles share name '{n1}'")

    # --- Cluster shuffle consistency ---
    pair_id_order = tuple(p["pair_id"] for p in regular_pairs)
    if cluster_index not in cluster_shuffles:
        cluster_shuffles[cluster_index] = pair_id_order
    elif cluster_shuffles[cluster_index] != pair_id_order:
        errors.append(f"Group {group} (cluster {cluster_index}): "
                      f"pair_id order differs from first group in cluster")

# --- Real pair 40/40 split ---
for key in ["riley_graham", "daniel_samantha"]:
    count = real_pair_counts.get(key, 0)
    if count != 40:
        warnings.append(f"Real pair '{key}' appears {count} times (expected 40)")

# --- Print results ---
print("=" * 60)
print("VERIFICATION RESULTS")
print("=" * 60)
if errors:
    print(f"FAILED — {len(errors)} error(s) found:")
    for e in errors:
        print(f"  ✗ {e}")
else:
    print("PASSED — No errors found.")

if warnings:
    print(f"\n{len(warnings)} warning(s):")
    for w in warnings:
        print(f"  ⚠ {w}")

print("=" * 60)

summary_lines = []

def sline(text=""):
    summary_lines.append(text)

total_groups = len(output)

# Header
sline("=" * 60)
sline("RANDOMIZATION SUMMARY REPORT")
sline(f"Groups: {total_groups}  |  Pairs: {len(all_pair_ids)}")
sline("=" * 60)

# ----------------------------
# 1. Grand total vs target
# ----------------------------
# Each pair appears once per group, 24 pairs x 80 groups = 1920 total assignments
total_assignments = len(all_pair_ids) * total_groups
targets_grand = {
    "M/F": total_assignments * 0.375,   # 9/24
    "F/M": total_assignments * 0.375,   # 9/24
    "M/M": total_assignments * 0.125,   # 3/24
    "F/F": total_assignments * 0.125,   # 3/24
}
grand = {"M/F": 0, "F/M": 0, "M/M": 0, "F/F": 0}
for pid in all_pair_ids:
    for combo in grand:
        grand[combo] += gender_summary[pid][combo]
grand_total = sum(grand.values())

sline()
sline("1. GRAND TOTAL VS TARGET")
sline("-" * 60)
sline(f"{'Combo':<8} {'Actual':>8} {'Target':>8} {'Delta':>8} {'Pct':>8}")
sline("-" * 60)
for combo in ["M/F", "F/M", "M/M", "F/F"]:
    delta = grand[combo] - targets_grand[combo]
    pct = grand[combo] / grand_total * 100
    sline(f"{combo:<8} {grand[combo]:>8} {targets_grand[combo]:>8.1f} {delta:>+8.1f} {pct:>7.1f}%")

# ----------------------------
# 2. Per-pair-id gender counts
# ----------------------------
sline()
sline("2. GENDER COUNTS BY PAIR ID")
sline("-" * 60)
sline(f"{'PairID':<8} {'F/F':>6} {'M/F':>6} {'M/M':>6} {'F/M':>6} {'Total':>6} {'MM+FF':>6}")
sline("-" * 60)
for pid in sorted(all_pair_ids):
    c = gender_summary[pid]
    total = sum(c.values())
    sline(f"{pid:<8} {c['F/F']:>6} {c['M/F']:>6} {c['M/M']:>6} {c['F/M']:>6} {total:>6} {c['M/M']+c['F/F']:>6}")

# ----------------------------
# 3. GPA BY GENDER COMBO
# ----------------------------
gpa_by_combo = defaultdict(list)
gpa_by_pair_combo = defaultdict(lambda: defaultdict(list))

for group, pairs in output.items():
    for pair in pairs:
        if pair["pair_id"] == REAL_PAIR_ID:
            continue
        pid = pair["pair_id"]
        combo_key = f"{pair['profile_1']['gender']}/{pair['profile_2']['gender']}"
        for profile_key in ["profile_1", "profile_2"]:
            gpa = pair[profile_key]["gpa"]
            gpa_by_combo[combo_key].append(gpa)
            gpa_by_pair_combo[pid][combo_key].append(gpa)

sline()
sline("3. GPA BY GENDER COMBO")
sline("-" * 60)
sline("  Average GPA across all pairs by gender combo:")
sline(f"  {'Combo':<8} {'N':>6} {'Mean GPA':>10} {'Min':>8} {'Max':>8}")
sline("  " + "-" * 44)
for combo in ["M/F", "F/M", "M/M", "F/F"]:
    gpas = gpa_by_combo[combo]
    if gpas:
        sline(f"  {combo:<8} {len(gpas):>6} {sum(gpas)/len(gpas):>10.4f} {min(gpas):>8.4f} {max(gpas):>8.4f}")
    else:
        sline(f"  {combo:<8} {'0':>6} {'N/A':>10}")

sline()
sline("  Mean GPA per pair_id by gender combo:")
sline(f"  {'PairID':<8} {'M/F':>8} {'F/M':>8} {'M/M':>8} {'F/F':>8}")
sline("  " + "-" * 40)
for pid in sorted(all_pair_ids):
    vals = []
    for combo in ["M/F", "F/M", "M/M", "F/F"]:
        gpas = gpa_by_pair_combo[pid][combo]
        vals.append(f"{sum(gpas)/len(gpas):.3f}" if gpas else "  N/A")
    sline(f"  {pid:<8} {vals[0]:>8} {vals[1]:>8} {vals[2]:>8} {vals[3]:>8}")

# ----------------------------
# 4. Group-level balance (replaces session-level)
# ----------------------------
sline()
sline("4. GROUP-LEVEL BALANCE")
sline("-" * 60)
sline(f"{'Group':<10} {'M/F':>6} {'F/M':>6} {'M/M':>6} {'F/F':>6} {'Total':>6}")
sline("-" * 60)
for group in sorted(output.keys()):
    c = {"M/F": 0, "F/M": 0, "M/M": 0, "F/F": 0}
    for pair in output[group]:
        if pair["pair_id"] == REAL_PAIR_ID:
            continue
        key = f"{pair['profile_1']['gender']}/{pair['profile_2']['gender']}"
        c[key] += 1
    total = sum(c.values())
    sline(f"{group:<10} {c['M/F']:>6} {c['F/M']:>6} {c['M/M']:>6} {c['F/F']:>6} {total:>6}")

# ----------------------------
# 5. NAME USAGE SUMMARY
# ----------------------------
name_counts = defaultdict(int)
name_gender = {}

for group, pairs in output.items():
    for pair in pairs:
        if pair["pair_id"] == REAL_PAIR_ID:
            continue
        for profile_key in ["profile_1", "profile_2"]:
            p = pair[profile_key]
            name_counts[p["name"]] += 1
            name_gender[p["name"]] = p["gender"]

sline()
sline("5. NAME USAGE SUMMARY")
sline("-" * 60)
sline(f"{'Name':<20} {'Gender':>8} {'Count':>8}")
sline("-" * 60)
for name, count in sorted(name_counts.items(), key=lambda x: (-x[1], x[0])):
    sline(f"{name:<20} {name_gender[name]:>8} {count:>8}")

# Name reuse within group (count > 2 flagged)
sline()
sline("  Name reuse within group (count > 2 flagged):")
sline(f"  {'Group':<10} {'Name':<20} {'Gender':>8} {'Count':>8}")
sline("  " + "-" * 44)
any_reuse = False
for group in sorted(output.keys()):
    group_name_counts = defaultdict(int)
    group_name_gender = {}
    for pair in output[group]:
        if pair["pair_id"] == REAL_PAIR_ID:
            continue
        for profile_key in ["profile_1", "profile_2"]:
            p = pair[profile_key]
            group_name_counts[p["name"]] += 1
            group_name_gender[p["name"]] = p["gender"]
    repeats = {n: c for n, c in group_name_counts.items() if c > 2}
    if repeats:
        any_reuse = True
        for name, count in sorted(repeats.items(), key=lambda x: -x[1]):
            sline(f"  {group:<10} {name:<20} {group_name_gender[name]:>8} {count:>8}")
if not any_reuse:
    sline("  No name reuse above threshold detected across any group.")

# ----------------------------
# 6. GROUP DETAIL (replaces session x group)
# ----------------------------
sline()
sline("6. GROUP DETAIL")
sline("-" * 60)
sline(f"{'Group':<10} {'M/F':>6} {'F/M':>6} {'M/M':>6} {'F/F':>6} {'Total':>6} {'RealPair':>12}")
sline("-" * 60)
for group in sorted(output.keys()):
    c = {"M/F": 0, "F/M": 0, "M/M": 0, "F/F": 0}
    real_pair_name = "N/A"
    for pair in output[group]:
        if pair["pair_id"] == REAL_PAIR_ID:
            real_pair_name = pair.get("real_pair", "N/A")
            continue
        key = f"{pair['profile_1']['gender']}/{pair['profile_2']['gender']}"
        c[key] += 1
    total = sum(c.values())
    sline(f"{group:<10} {c['M/F']:>6} {c['F/M']:>6} {c['M/M']:>6} {c['F/F']:>6} {total:>6} {real_pair_name:>12}")

sline()
sline("=" * 60)

# ----------------------------
# 7. VERIFICATION CHECKS
# ----------------------------
sline()
sline("7. VERIFICATION CHECKS")
sline("-" * 60)

if errors:
    sline(f"FAILED -- {len(errors)} error(s) found:")
    for e in errors:
        sline(f"  x {e}")
else:
    sline("PASSED -- No errors found.")

if warnings:
    sline(f"")
    sline(f"  {len(warnings)} warning(s):")
    for w in warnings:
        sline(f"  ! {w}")
else:
    sline("No warnings.")

sline()
sline(f"  Real pair distribution:")
sline(f"  {'Key':<20} {'Count':>6} {'Expected':>10}")
sline("  " + "-" * 38)
for key in ["riley_graham", "daniel_samantha"]:
    count = real_pair_counts.get(key, 0)
    sline(f"  {key:<20} {count:>6} {'40':>10}")

sline()
sline("=" * 60)

# ----------------------------
# 8. ADJACENT GROUP PAIR OVERLAP
# ----------------------------
sline()
sline("8. ADJACENT GROUP PAIR OVERLAP")
sline("-" * 60)
sline("  Checks how many (pair_id, gender_combo) assignments are")
sline("  identical between each adjacent group pair (0-1, 2-3, ...).")
sline("-" * 60)
sline(f"  {'Groups':<12} {'Matches':>8} {'Out Of':>8} {'Pct':>8}")
sline("  " + "-" * 40)

overlap_counts = []

for base in range(0, len(output), 2):
    next_group = base + 1
    if next_group not in output:
        break

    # Build (pair_id, gender_combo) sets for each group, excluding real pair
    def get_combo_set(group):
        return {
            (p["pair_id"], tuple(p["gender_combo"]))
            for p in output[group]
            if p["pair_id"] != REAL_PAIR_ID
        }

    combos_base = get_combo_set(base)
    combos_next = get_combo_set(next_group)

    matches = len(combos_base & combos_next)
    total = len(combos_base)
    pct = matches / total * 100 if total > 0 else 0
    overlap_counts.append(matches)

    sline(f"  {f'{base}-{next_group}':<12} {matches:>8} {total:>8} {pct:>7.1f}%")

sline()
sline(f"  Summary:")
sline(f"  Min matches:  {min(overlap_counts)}")
sline(f"  Max matches:  {max(overlap_counts)}")
sline(f"  Mean matches: {sum(overlap_counts)/len(overlap_counts):.2f}")

sline()
sline("=" * 60)

summary_path = "randomization_checks/randomization_summary.txt"
with open(summary_path, "w", encoding="utf-8") as f:
    f.write("\n".join(summary_lines))

print(f"Randomization summary written to {summary_path}")

