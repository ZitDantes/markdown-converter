#!/usr/bin/env bash
# Hook Cursor sessionStart : injecte un résumé d'état du projet (contexte système).
set +e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)" || exit 1
cd "$ROOT" || exit 1

# Lance une commande, capture stdout dans une variable, tue le processus après `seconds` (réseau / CI).
_cmd_timeout_capture() {
  local seconds="$1"
  shift
  local outf
  outf="$(mktemp "${TMPDIR:-/tmp}/cursor-hook-session-init.XXXXXX")" || {
    echo ""
    return 127
  }
  "$@" >"$outf" 2>/dev/null &
  local pid=$!
  (
    sleep "$seconds"
    kill -TERM "$pid" 2>/dev/null
    sleep 2
    kill -KILL "$pid" 2>/dev/null
  ) &
  local killer=$!
  wait "$pid" 2>/dev/null
  local ec=$?
  kill "$killer" 2>/dev/null
  wait "$killer" 2>/dev/null
  cat "$outf" 2>/dev/null || true
  rm -f "$outf"
  return "$ec"
}

# Consommer stdin (JSON Cursor) sans bloquer si le flux ne se ferme pas (ex. sandbox).
if [ ! -t 0 ]; then
  python3 -c '
import select, sys
try:
    if select.select([sys.stdin], [], [], 2.0)[0]:
        sys.stdin.read(10_000_000)
except Exception:
    pass
' 2>/dev/null || true
fi

# --- 1. Git ---
branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")"
commit_info="$(git log -1 --format='%s — %ci' 2>/dev/null || echo "inconnu")"
LINE_GIT="Git : branche « ${branch} », dernier commit : ${commit_info}"

# --- 2. CI (gh) ---
LINE_CI="CI : statut inconnu."
if command -v gh >/dev/null 2>&1; then
  # Évite les invites interactives ; borne le temps d'attente réseau.
  gh_json="$(_cmd_timeout_capture 15 env GH_PROMPT_DISABLED=1 gh run list --limit 1 --json status,conclusion,name)"
  gh_ec=$?
  if [ "$gh_ec" -ne 0 ] || [ -z "$gh_json" ]; then
    LINE_CI="CI : statut inconnu (gh inaccessible ou non authentifié)."
  elif [ "$gh_json" = "[]" ]; then
    LINE_CI="CI : statut inconnu (aucun run récent listé)."
  else
    export GH_RUN_JSON="$gh_json"
    LINE_CI="$(python3 -c "
import json, os
raw = os.environ.get('GH_RUN_JSON', '')
try:
    runs = json.loads(raw)
    if not runs:
        print('CI : statut inconnu (réponse vide).')
    else:
        d = runs[0]
        name = d.get('name') or '?'
        status = d.get('status') or '?'
        concl = d.get('conclusion')
        if concl == 'success':
            etat = 'vert (succès)'
        elif concl in ('failure', 'timed_out'):
            etat = 'rouge (échec)'
        elif concl in ('cancelled', 'skipped', 'action_required', 'neutral'):
            etat = f'terminé ({concl})'
        elif status in ('queued', 'in_progress', 'waiting', 'requested', 'pending'):
            etat = 'en cours'
        elif concl is None and status:
            etat = f'en cours (status={status})'
        else:
            etat = 'statut inconnu'
        print(f'CI : dernier workflow « {name} » — {etat}.')
except Exception:
    print('CI : statut inconnu (réponse gh illisible).')
")"
    unset GH_RUN_JSON 2>/dev/null || true
  fi
else
  LINE_CI="CI : statut inconnu (gh non installé)."
fi

# --- 3. Ruff ---
LINE_RUFF="Ruff : statut inconnu (commande absente)."
if command -v ruff >/dev/null 2>&1; then
  ruff_out="$(_cmd_timeout_capture 45 ruff check . --output-format=json)"
  ruff_ec=$?
  if ! printf '%s' "$ruff_out" | python3 -c "import json,sys; json.load(sys.stdin)" 2>/dev/null; then
    LINE_RUFF="Ruff : statut inconnu (sortie invalide ou ruff en erreur fatale)."
  else
    n="$(printf '%s' "$ruff_out" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null)"
    if [ -z "$n" ]; then
      LINE_RUFF="Ruff : statut inconnu."
    elif [ "$n" -eq 0 ] && [ "$ruff_ec" -eq 0 ]; then
      LINE_RUFF="Ruff : propre."
    elif [ "$n" -gt 0 ]; then
      LINE_RUFF="Ruff : ${n} erreur(s)."
    else
      LINE_RUFF="Ruff : signalé en erreur (${n} diagnostic(s))."
    fi
  fi
fi

# --- 4. Fichiers non commités ---
status_short="$(git status --short 2>/dev/null || true)"
if [ -z "$status_short" ]; then
  LINE_WT="Fichiers : rien de non commité."
else
  nlines="$(printf '%s\n' "$status_short" | wc -l | tr -d ' ')"
  LINE_WT="Fichiers : ${nlines} entrée(s) modifiée(s) / non suivie(s) (git status --short)."
fi

LINE_Q="Sur quoi travaille-t-on maintenant ?"

export HOOK_LINE_GIT="$LINE_GIT"
export HOOK_LINE_CI="$LINE_CI"
export HOOK_LINE_RUFF="$LINE_RUFF"
export HOOK_LINE_WT="$LINE_WT"
export HOOK_LINE_Q="$LINE_Q"

python3 -c "
import json, os
ctx = '\n'.join([
    os.environ.get('HOOK_LINE_GIT', ''),
    os.environ.get('HOOK_LINE_CI', ''),
    os.environ.get('HOOK_LINE_RUFF', ''),
    os.environ.get('HOOK_LINE_WT', ''),
    os.environ.get('HOOK_LINE_Q', ''),
])
print(json.dumps({'additional_context': ctx}, ensure_ascii=False))
"
exit 0
