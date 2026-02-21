# Commit Checklist Final (sem commit automatico)

Checklist objetivo para fechar o estado do repo antes de commitar.

## 1) Documentacao
- [ ] `README.md` atualizado para estado atual.
- [ ] `docs/notes/METHODOLOGY.md` e `docs/notes/SCOPE.md` coerentes com o que roda hoje.
- [ ] `docs/notes/MAC_HANDOFF.md` atualizado para continuidade operacional.
- [ ] `docs/INDEX.md` revisado (sem links quebrados).

## 2) Engine e scripts
- [ ] Scripts novos usam `engine.*` (sem dependencia nova em `spa.*`/`graph_engine.*`).
- [ ] Wrappers de compatibilidade continuam funcionando.
- [ ] Fluxo oficial documentado bate com scripts reais em `scripts/ops/`.

## 3) Operacao e validacao
- [ ] Pipeline diario roda sem erro.
- [ ] Snapshot valido gerado em `results/ops/snapshots/<run_id>/`.
- [ ] Contrato de saida validado.
- [ ] Diff de drift gerado e sem bloqueio inesperado.
- [ ] `audit_pack.json` presente no run.

## 4) Frontend/API
- [ ] `website-ui` builda/linta sem erro.
- [ ] Endpoints criticos respondem:
  - [ ] `/api/run/latest`
  - [ ] `/api/assets`
  - [ ] `/api/risk-truth`
- [ ] UI respeita gate (`validated/watch/inconclusive`) e modo diagnostico.

## 5) Higiene de repositorio
- [ ] Sem artefato temporario na raiz.
- [ ] Itens nao operacionais movidos para `legacy/` quando aplicavel.
- [ ] `.gitignore` cobre caches e pastas de build.
- [ ] `git status` revisado arquivo a arquivo antes do commit.

## 6) Preparacao de rename (A-firma -> Assyntrax)
- [ ] Docs e referencias textuais com nome alvo ajustadas.
- [ ] Plano de update de remote preparado.
- [ ] Tasks agendadas revisadas para caminho/nome final.
