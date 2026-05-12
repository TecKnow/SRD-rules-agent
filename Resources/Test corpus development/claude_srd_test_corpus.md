# D&D SRD 5.2.1 Test Question Corpus (100 Questions)

**Authoritative source:** *System Reference Document 5.2.1* (SRD 5.2.1), Wizards of the Coast LLC, released April 22, 2025 and updated May 1, 2025 — confirmed by D&D Beyond's official forum announcement: "SRD 5.2.1 Update (5/1/2025): An update to the SRD has been published that includes the 15 magic items mistakenly omitted from version 5.2, as well as other corrections." Licensed under CC-BY-4.0. Available at https://www.dndbeyond.com/srd; PDF at https://media.dndbeyond.com/compendium-images/srd/5.2/SRD_CC_v5.2.1.pdf. All page references in this document are to that PDF unless stated otherwise. Where the term "PHB 2024" is used, it refers to the *Dungeons & Dragons Player's Handbook* (2024) — content from that book is NOT necessarily in SRD 5.2.1; many sections of the PHB are excluded from the SRD for IP/branding reasons (per WotC's official FAQ at dndbeyond.com/srd).

**Distribution:** 50 rules-spread (Q1–50), 25 version-specific (Q51–75), 15 common (Q76–90), 10 contentious (Q91–100).

**Universal grading note (applies to every answer):** Full credit requires (a) explicit reliance on SRD 5.2.1 text, (b) refusing to silently import 2014 / SRD 5.1 rules, (c) flagging when a rule, monster, class, species, or spell is in the 2024 PHB but EXCLUDED from SRD 5.2.1 (per Wizards' FAQ: "SRD 5.2 includes a wide range of content from the 2024 core rulebooks, but some classes (such as the Artificer), species (like Aasimar), and monsters (including the Beholder) have been excluded. These exclusions are based on brand identity protection, licensing strategy, and intellectual property rights"), and (d) refusing to import Pathfinder defaults.

---

## CATEGORY 1 — RULES-SPREAD (Q1–50)

### Q1 (rules-spread) — Divine Smite + opportunity attack + thrown weapon
**Q.** Can a Paladin use the Divine Smite spell on an Opportunity Attack made with a thrown dagger?
**A.** No, on two independent grounds. (1) Opportunity Attacks require *melee* attacks. SRD 5.2.1, "Opportunity Attacks": "To make the attack, take a Reaction to make one melee attack with a weapon or an Unarmed Strike against that creature." A thrown dagger makes a *ranged* attack, not a melee attack — the Thrown property states "you can throw the weapon to make a ranged attack." So you cannot make a thrown attack as an OA at all. (2) Even if a thrown OA were allowed by some reading, Divine Smite's casting time is "1 Bonus Action, which you take immediately after hitting a target with a Melee weapon or an Unarmed Strike." A thrown attack is not a melee attack regardless of the weapon's table classification, so Smite would not trigger.
**SRD passages.** Divine Smite (1st-level Paladin spell): "Casting Time: 1 Bonus Action, which you take immediately after hitting a target with a Melee weapon or an Unarmed Strike. … The target takes an extra 2d8 Radiant damage from the attack. The damage increases by 1d8 if the target is a Fiend or an Undead." Opportunity Attacks (Combat, p. 15). Thrown property (Equipment).
**Common wrong answers.** "Yes, daggers are Melee weapons, so it counts" (conflates table classification with attack type); "Yes, like in 2014" (in 2014 Divine Smite was a class feature triggered by *any* melee weapon attack and there was no Bonus Action restriction).
**Rubric.** Full credit requires: (a) identifying that OAs must be melee attacks; (b) noting the Thrown property turns the attack ranged; (c) noting Divine Smite requires hitting with a Melee weapon or Unarmed Strike; (d) concluding the smite cannot be used.

### Q2 (rules-spread) — Wild Shape, Beast Spells, Misty Step, breaking a grapple
**Q.** A Druid is Wild Shaped into a wolf, then is Grappled. Can they Misty Step (via Beast Spells) to break the grapple?
**A.** Two-part answer. (1) On the rules-of-grapple side, *if* the Druid teleports out of the grappler's reach, the grapple ends — the Grappled condition ends "if the distance between the Grappled target and the grappler exceeds the grapple's range," and Teleport doesn't provoke OAs. (2) Critically, **Beast Spells is NOT in SRD 5.2.1.** SRD 5.2.1's only Druid subclass is Circle of the Land (p. 46); it does not grant Beast Spells. The base Druid class in the SRD does not include the Beast Spells feature either. So a Wild Shaped Druid in SRD 5.2.1 cannot cast Misty Step while transformed. The agent should flag this as an attempt to use 2024-PHB-but-not-SRD content.
**SRD passages.** Grappled (Conditions): "Speed 0… The grappler can drag or carry you when it moves… [the condition ends] if the distance between the Grappled target and the grappler exceeds the grapple's range." Druid (p. 41–46): no Beast Spells feature in the SRD.
**Common wrong answers.** "Yes, Beast Spells lets the Druid cast" (importing 2024 PHB content not in SRD).
**Rubric.** Full credit: (a) flag Beast Spells as outside SRD 5.2.1; (b) state that *if* the Druid could teleport, range-exceedance would end the grapple.

### Q3 (rules-spread) — Magic Resistance + Heightened Spell
**Q.** A creature with Magic Resistance is targeted by a Sorcerer using Heightened Spell on a save-based spell. Net effect on the save?
**A.** A straight d20 roll (no Advantage, no Disadvantage). Magic Resistance: "The creature has Advantage on saving throws against spells and other magical effects." Heightened Spell (Metamagic, p. 66): "When you cast a Spell that forces a creature to make a Saving Throw, you can spend 2 Sorcery Points to give one target of the spell Disadvantage on its first Saving Throw made against the spell." Per Advantage/Disadvantage (p. 8): "If circumstances cause a roll to have both Advantage and Disadvantage, the roll has neither of them, and you roll one d20. This is true even if multiple circumstances impose Disadvantage and only one grants Advantage or vice versa."
**Common wrong answers.** "The Disadvantage cancels one of the two Advantages" (no — the rule is binary, not numeric).
**Rubric.** Full credit: (a) cite Heightened Spell; (b) cite Magic Resistance; (c) cite the no-stacking rule and conclude a single d20.

### Q4 (rules-spread) — Sneak Attack with thrown weapons
**Q.** Can a Rogue Sneak Attack with a thrown handaxe in SRD 5.2.1?
**A.** This is a known ambiguity. Sneak Attack requires "a Finesse weapon or a Ranged weapon." The handaxe is on the *Melee* weapons table but has the Thrown property with a range. There is no glossary definition of "Ranged weapon" beyond table classification. Strict reading: a handaxe is a Melee weapon, so it doesn't qualify (handaxe also lacks Finesse). Looser reading common in 2024-rules tables: a thrown weapon is making a ranged *attack* and is therefore a "Ranged weapon" for Sneak Attack purposes. The agent should present both. Daggers (Melee + Finesse) qualify under either reading because of Finesse. Tridents (Melee + Thrown, no Finesse) face the same ambiguity as the handaxe.
**Rubric.** Full credit: present both readings; cite Sneak Attack text and the Thrown property.

### Q5 (rules-spread) — Improved Critical + Vex
**Q.** A Champion Fighter has Improved Critical and is wielding a Vex-mastery weapon. After hitting, does Vex's "Advantage on next attack" interact with the 19-crit threshold to make a second crit "auto-confirm"?
**A.** No. There is no "crit confirmation" mechanic in 5e/5.5e at all. Improved Critical (Champion, p. 49) lowers the crit threshold to 19 or 20. Vex (p. 90): "If you hit a creature with this weapon and deal damage to the creature, you have Advantage on your next attack roll against that creature before the end of your next turn." Advantage doesn't convert hits to crits; it just rolls 2d20. Statistically, a 19-or-20 crit with Advantage is much more likely (~19% vs. ~10%), but each die is evaluated independently.
**Common wrong answers.** "Auto-confirms a crit" (Pathfinder/3.5e default).
**Rubric.** Full credit: (a) cite Improved Critical's threshold; (b) cite Vex; (c) deny the auto-confirm framing.

### Q6 (rules-spread) — Spellcasting under Restrained, Grappled, Silenced
**Q.** A Bard casting a Verbal-component spell is Restrained, Grappled, and Silenced. Which condition prevents the cast?
**A.** Only Silence prevents Verbal components. Restrained (Conditions): "Speed 0… Disadvantage on attack rolls… Disadvantage on Dexterity saving throws." Grappled: "Speed 0… Disadvantage on attack rolls against any target other than the grappler." Neither condition mentions speech. Silence (the area effect) prevents speaking, blocking Verbal components. Note that Silenced is *not* a separate condition in SRD 5.2.1; rather, an area of magical silence (e.g., the Silence spell) prevents speech.
**Common wrong answer.** "Restrained or Grappled prevent somatic components" — false in SRD 5.2.1.
**Rubric.** Full credit: identify only Silence as a blocker; cite the conditions to confirm they don't block speech.

### Q7 (rules-spread) — Topple weapon mastery via Opportunity Attack against Magic Resistance
**Q.** Does Topple work on an Opportunity Attack with a Glaive against a creature with Magic Resistance?
**A.** Yes, and Magic Resistance does NOT apply. Topple triggers on a hit with the weapon; an OA is one melee attack with the weapon. Topple forces a Constitution saving throw. Magic Resistance gives Advantage on saves "against spells and other magical effects." Topple is a mundane weapon mastery, not a spell or magical effect. The save is rolled normally. DC = 8 + ability modifier used for the attack + Proficiency Bonus.
**SRD passage.** Topple (p. 90): "If you hit a creature with this weapon, you can force the creature to make a Constitution saving throw (DC 8 plus the ability modifier used to make the attack roll and your Proficiency Bonus). On a failed save, the creature has the Prone condition."
**Rubric.** Full credit: (a) Topple on OA hit; (b) Magic Resistance doesn't apply (mundane); (c) correct DC.

### Q8 (rules-spread) — Warlock Pacts and Eldritch Invocations in SRD
**Q.** Are Pact of the Tome / Pact of the Blade / Pact of the Chain in SRD 5.2.1?
**A.** SRD 5.2.1's only Warlock subclass is **Fiend Patron** (p. 76). The 2024 PHB integrated Pact Boons into Eldritch Invocations rather than as separate features. SRD 5.2.1 has an Eldritch Invocation Options section (p. 72). The agent should verify the specific invocations against the SRD; the structural change is that Pacts are no longer a level-3 binary choice but invocation options.
**Rubric.** Full credit: identify Fiend Patron as only subclass; identify Pacts-as-invocations structure.

### Q9 (rules-spread) — Grapple a flying dragon, then drop to ground
**Q.** A Medium Paladin grapples a Large dragon while it's flying. What happens?
**A.** (1) Allowed: "no more than one size larger than you" — Medium → Large is exactly one size larger. (2) Grappled imposes Speed 0 on the dragon (including its Fly Speed). A flying creature with Speed 0 falls (unless it has Hover). (3) The Paladin is on/grappling the dragon; the Paladin is also airborne and not flying themselves, so the Paladin descends with the dragon. (4) Falling damage: 1d6 Bludgeoning per 10 feet, max 20d6 (Falling, Hazards / Rules Glossary). (5) When the grapple ends (e.g., by dragon escaping), the dragon may resume flight if it has movement; the Paladin continues to fall.
**Rubric.** Full credit: (a) cite grapple size limit; (b) cite Speed 0; (c) note falling rule; (d) describe Paladin's descent.

### Q10 (rules-spread) — Spirit Guardians + forced movement
**Q.** Does Spirit Guardians damage a creature pushed into its area by Thunderwave?
**A.** Yes. Spirit Guardians' trigger language is broader than 2014's "starts its turn" — it applies when a creature "enters the spell's area for the first time on a turn." That phrasing covers any creature's turn (ally's, enemy's, or the caster's). Forced movement during another creature's turn that brings the target into the aura triggers damage.
**Rubric.** Full credit: identify "on a turn" trigger; conclude forced movement triggers damage.

### Q11 (rules-spread) — Flurry of Blows + bonus action spells
**Q.** A Monk uses Flurry of Blows after the Attack action. Can they also cast a Bonus-Action spell?
**A.** No. Flurry of Blows costs a Bonus Action. Bonus Actions (p. 10): "You can take only one Bonus Action on your turn, so you must choose which Bonus Action to use if you have more than one available." A second Bonus-Action spell is foreclosed.
**Rubric.** Full credit: cite the once-per-turn Bonus Action limit.

### Q12 (rules-spread) — Frenzy bonus-action attack and Cleave's "once per turn"
**Q.** A Berserker Frenzying with a Cleave-mastery weapon: does Cleave trigger from the Frenzy attack? Can Cleave trigger twice in a turn?
**A.** Yes, Cleave can trigger from a Frenzy bonus-action attack — the trigger is "if you hit a creature with a melee attack using this weapon," not "during the Attack action." However, Cleave is "once per turn" regardless of which attack triggers it. So whether Cleave triggers from an Extra Attack or from Frenzy, only one Cleave per turn.
**Rubric.** Full credit: (a) Frenzy attack can trigger Cleave; (b) Cleave is once per turn total.

### Q13 (rules-spread) — Help action and saving throws
**Q.** Can the Help action grant Advantage on a saving throw?
**A.** No. Help (Actions, p. 10): "Help another creature's ability check or attack roll, or administer first aid." Saves are not listed.
**Rubric.** Full credit: quote Help; deny saves.

### Q14 (rules-spread) — Damage modifier order with Resistance and saves
**Q.** A Tiefling (Fire Resistance) takes 28 Fire damage from a Fireball, succeeds on Dex save (half). What's the damage taken?
**A.** 7. Order of Application (p. 17): adjustments first, Resistance second, Vulnerability third. Successful save halves to 14; Fire Resistance halves again to 7.
**Rubric.** Full credit: cite order; show 28 → 14 → 7.

### Q15 (rules-spread) — Stunned and speech / spellcasting
**Q.** A Stunned creature: can they speak? Can they cast spells?
**A.** Stunned (Conditions): imposes Incapacitated; auto-fails Strength and Dexterity saves; attacks against you have Advantage. Incapacitated (Conditions): "You can't take any action, Bonus Action, or Reaction." So no spellcasting (which requires an action / Bonus Action / Reaction). On speech: SRD 5.2.1's Stunned text does NOT explicitly forbid speech (unlike 2014's Stunned, which read "can speak only falteringly"). Incapacitated also does not address speech directly. So in SRD 5.2.1, a Stunned creature is not silenced *per se*, but cannot cast spells because of the Incapacitated foundation.
**Rubric.** Full credit: (a) Incapacitated denies actions/casting; (b) flag the speech change from 2014.

### Q16 (rules-spread) — Twinned Spell + Hold Person
**Q.** A Sorcerer Twinned-Spells Hold Person. Does it work?
**A.** Yes at 2nd level (single target). Twinned Spell (p. 66): "When you cast a spell that has a single target and doesn't have a range of self… you can spend Sorcery Points equal to twice the spell's level to target a second creature in range with the same spell." If upcast for multiple targets, Twinned Spell does not apply.
**Rubric.** Full credit: (a) base 2nd-level Hold Person is single target; (b) upcasting forfeits Twinned eligibility.

### Q17 (rules-spread) — Restrained + Grappled
**Q.** Restrained AND Grappled — do effects stack?
**A.** No. Speed 0 from either is still 0. Disadvantage from either doesn't stack — Advantage/Disadvantage is binary. The conditions overlap mechanically but don't compound.
**Rubric.** Full credit: cite no-stacking rule; explicit non-stacking conclusion.

### Q18 (rules-spread) — Sacred Weapon and thrown attacks
**Q.** Does Channel Divinity: Sacred Weapon (Oath of Devotion) apply when the weapon is thrown?
**A.** Yes. Sacred Weapon refers to "the weapon" generally, not "melee attacks with the weapon." The Cha bonus to attack and Radiant damage type apply to any attack with that weapon, including thrown attacks.
**Rubric.** Full credit: quote Sacred Weapon; conclude applies to thrown.

### Q19 (rules-spread) — Flying through difficult terrain
**Q.** Does flying through Difficult Terrain cost extra movement?
**A.** Yes, by default. Difficult Terrain rule: "Every foot of movement in Difficult Terrain costs 1 extra foot." There is an explicit carve-out for Climb Speed when climbing, but NO carve-out for Fly Speed. So a creature flying through difficult terrain (e.g., dense smoke, magical hindering area) pays double.
**Rubric.** Full credit: cite Difficult Terrain; identify absence of Fly Speed exemption.

### Q20 (rules-spread) — Concentration on Hunter's Mark at Ranger 13+
**Q.** At Ranger 13, does taking damage break Concentration on Hunter's Mark?
**A.** No. Relentless Hunter (Ranger 13): "Taking damage can't break your Concentration on Hunter's Mark." Other Concentration-enders (incapacitation, casting another Concentration spell, dying) still apply.
**Rubric.** Full credit: cite Relentless Hunter; note other enders still active.

### Q21 (rules-spread) — Misty Step ending a grapple
**Q.** Does Misty Step end a grapple?
**A.** Yes (assuming destination is outside grappler's reach). Grappled ends when distance exceeds grapple's range. Teleport: 30 ft, doesn't provoke OAs.
**Rubric.** Full credit: cite Grappled-end clause + teleport-no-OA rule.

### Q22 (rules-spread) — Truesight vs. Mirror Image
**Q.** Does Truesight bypass Mirror Image?
**A.** Likely yes, but with ambiguity. Truesight (Rules Glossary): grants the ability to "automatically detect visual illusions and succeed on saving throws against them." Mirror Image is broadly considered a visual illusion (creates illusory duplicates). SRD 5.2.1 doesn't explicitly classify Mirror Image as a "visual illusion" in its spell description. Most rulings: Truesight ignores Mirror Image. Agent should note the ambiguity.
**Rubric.** Full credit: cite Truesight; flag classification ambiguity.

### Q23 (rules-spread) — Charmed target and caster's Concentration
**Q.** A Cleric concentrating on Bless. One target gets Charmed. Does that break Bless?
**A.** No. Conditions on a target don't affect the caster's Concentration. Concentration ends only on the caster's loss of focus (incapacitation, damage Con-save failure, casting another Concentration spell, etc.).
**Rubric.** Full credit: clarify caster vs. target conditions.

### Q24 (rules-spread) — Tiny familiar in caster's space, providing cover
**Q.** Can a Tiny familiar share space and provide Half Cover to the Wizard?
**A.** Tiny ally can share space without it counting as Difficult Terrain. But for cover: Half Cover requires "Another creature or an object that covers at least half of the target." A Tiny creature (2½ × 2½ ft) cannot cover half of a Medium target. So no cover bonus.
**Rubric.** Full credit: (a) space-sharing OK; (b) Tiny is too small to grant Half Cover.

### Q25 (rules-spread) — Dodge vs. Constitution save
**Q.** Does Dodge help a Con save against a poison cloud?
**A.** No. Dodge: "Until the start of your next turn, attack rolls against you have Disadvantage, and you make Dexterity saving throws with Advantage." Only Dex saves benefit.
**Rubric.** Full credit: quote Dodge; deny Con-save benefit.

### Q26 (rules-spread) — Step of the Wind / Disengage scope
**Q.** Does a Bonus-Action Disengage prevent OAs for the entire turn?
**A.** Yes. Disengage (Actions, p. 10): "Your movement doesn't provoke Opportunity Attacks for the rest of the turn."
**Rubric.** Full credit: quote "rest of the turn."

### Q27 (rules-spread) — Pack Tactics vs. Three-Quarters Cover
**Q.** Pack Tactics (Advantage on attack with adjacent ally) against a target with Three-Quarters Cover (+5 AC) — what's the net?
**A.** Both apply independently. Attack rolled with Advantage; target has +5 AC. Cover is added to AC, not balanced against Advantage.
**Rubric.** Full credit: independent application of both modifiers.

### Q28 (rules-spread) — Aura of Protection while Grappled
**Q.** A Paladin is Grappled. Does Aura of Protection still emanate?
**A.** Yes. Aura of Protection (p. 53–55) deactivates only while the Paladin has the Incapacitated condition. Grappled does NOT impose Incapacitated. Aura emanates from the Paladin and moves with them.
**Rubric.** Full credit: identify Incapacitated as the only deactivator; Grappled ≠ Incapacitated.

### Q29 (rules-spread) — Petrified, Resistance to all damage, Critical Hit interaction
**Q.** A Petrified creature is hit by a Critical Hit. How is damage calculated?
**A.** Petrified gives Resistance to all damage. Order of Application: adjustments first (crit doubles dice), Resistance second. So roll doubled dice, sum, then halve. A 20-damage attack becomes 40 (crit), then 20 (Resistance).
**Rubric.** Full credit: cite Petrified Resistance; cite Order of Application; correct sequencing.

### Q30 (rules-spread) — Sculpt Spells on the caster
**Q.** Does Evoker's Sculpt Spells protect the Wizard themselves if they're in their own Fireball?
**A.** No. Sculpt Spells (p. 82): "When you cast an Evocation spell that affects other creatures you can see, you can choose a number of them equal to 1 + the spell's level; the chosen creatures automatically succeed on their saving throws against the spell, and they take no damage if they would normally take half damage on a successful save." "Other creatures" excludes self.
**Rubric.** Full credit: quote "other creatures"; explicit self-exclusion.

### Q31 (rules-spread) — Hide → Invisible → attack reveals
**Q.** A Rogue Hides as a Bonus Action (Cunning Action), then attacks. Advantage on the attack? Does Invisibility persist?
**A.** Advantage on the attack from the Invisible condition. After the attack roll resolves (hit or miss), the position is revealed: "If you are hidden when you make an attack roll, you give away your location when the attack hits or misses." So the Invisible condition ends after that single attack.
**Rubric.** Full credit: (a) Advantage on attack; (b) Invisible ends after attack.

### Q32 (rules-spread) — Forced movement of a grappler
**Q.** Can Thunderwave on the Roper end its grapple by pushing the Roper away?
**A.** Yes, if Thunderwave's push (10 ft on failed Strength save) exceeds the Roper's tendril range minus current distance. Grappled ends when distance exceeds grapple's range. The Roper's tendrils have substantial reach (per its stat block, p. 317); the agent should consult the Roper's specific tendril range.
**Rubric.** Full credit: identify range-exceedance trigger; conditional on push distance vs. tendril range.

### Q33 (rules-spread) — Druid metal armor restriction
**Q.** A Druid in metal armor casts Thunderwave. Mechanical effect?
**A.** None mechanical. The Druid description states Druids will not wear metal armor as a tradition; the SRD imposes no spell-failure or other mechanical penalty. The DM may impose narrative consequences.
**Rubric.** Full credit: identify the rule as flavor/tradition without mechanical penalty.

### Q34 (rules-spread) — Heightened Spell on multi-target spells
**Q.** Does Heightened Spell apply to all targets of Fireball?
**A.** No. "Give one target of the spell Disadvantage on its first Saving Throw."
**Rubric.** Full credit: quote "one target."

### Q35 (rules-spread) — Dark One's Blessing temp HP stacking
**Q.** Do temp HP from Dark One's Blessing stack with other temp HP?
**A.** No. Temporary Hit Points (p. 18): "Temporary Hit Points can't be added together. If you have Temporary Hit Points and receive more of them, you decide whether to keep the ones you have or to gain the new ones."
**Rubric.** Full credit: cite no-stack rule.

### Q36 (rules-spread) — Truesight in magical Darkness
**Q.** A creature with Truesight 60 ft attacks into a Darkness spell at 30 ft. Disadvantage?
**A.** No. Truesight pierces magical Darkness within range. No Heavily Obscured penalty.
**Rubric.** Full credit: cite Truesight; deny Disadvantage.

### Q37 (rules-spread) — Action Surge and Bonus Actions
**Q.** Does Action Surge grant a second Bonus Action?
**A.** No. Action Surge (Fighter, p. 47) grants "one additional action." Action ≠ Bonus Action. Bonus Action limit (one per turn) is unaffected.
**Rubric.** Full credit: distinguish action vs. Bonus Action.

### Q38 (rules-spread) — Quickened Fireball + Reaction Shield
**Q.** Quickened Fireball as a Bonus Action, and Shield as a Reaction later. Legal?
**A.** Yes. Shield is a Reaction, not constrained by the "one spell per turn" rule when its trigger occurs on someone else's turn. Even on the Sorcerer's own turn, Shield is triggered by an attack on the Sorcerer, which Shield can be cast in response to.
**Rubric.** Full credit: distinguish Reactions from Bonus-Action spells; cite the once-per-turn-spell rule.

### Q39 (rules-spread) — One-spell-per-turn rule in SRD 5.2.1
**Q.** Does the 2014 "Bonus-Action spell + cantrip with action" restriction still exist?
**A.** SRD 5.2.1 / 2024 PHB streamlined this. The general rule is now: "You can cast no more than one spell on each of your turns" (subject to verification of exact wording in SRD 5.2.1's Casting Spells section). This restriction is broader than 2014's specific rule.
**Rubric.** Full credit: identify the simplified rule; flag departure from 2014.

### Q40 (rules-spread) — Heavy Armor Master in SRD?
**Q.** Does a Barbarian's Rage stack with Heavy Armor Master against bludgeoning?
**A.** Heavy Armor Master is NOT in SRD 5.2.1. SRD 5.2.1's General Feats and Origin Feats are limited (Origin Feats: Alert, Magic Initiate, Savage Attacker, Skilled). The agent should flag this as content from the 2024 PHB but excluded from SRD.
**Rubric.** Full credit: flag Heavy Armor Master as outside SRD.

### Q41 (rules-spread) — Topple → Prone → crawl/stand-up costs
**Q.** A creature toppled Prone wants to stand up and attack. Costs?
**A.** Standing up costs half Speed (round down). Prone movement options: crawl (1 extra foot per foot) or stand. Once standing, full attack actions allowed. While Prone: Disadvantage on attacks; attackers within 5 ft have Advantage; attackers >5 ft have Disadvantage.
**Rubric.** Full credit: stand cost; crawl cost; Prone attack consequences.

### Q42 (rules-spread) — Push off a cliff
**Q.** Push mastery (10 ft) shoves target off a 30-ft cliff. Falling?
**A.** Yes. Falling: 1d6 Bludgeoning per 10 ft, max 20d6. 30-ft fall = 3d6.
**Rubric.** Full credit: cite Push; cite Falling.

### Q43 (rules-spread) — Long Jump distance and movement budget
**Q.** A Strength-16 character with 15 ft of remaining movement wants to Long Jump. Distance?
**A.** Per Long Jump (Rules Glossary): "When you make a Long Jump, you leap horizontally a number of feet up to your Strength score if you move at least 10 feet immediately before the jump… each foot you jump costs a foot of movement." The 10-ft run-up + jump distance are both deducted from movement. With 15 ft remaining, the character can use 10 ft for the run-up and jump up to 5 ft (with full Strength=16, they could otherwise jump up to 16 ft, but the jump itself costs movement). If the 10 ft run-up was already used earlier in the turn (i.e., 15 ft remaining is *after* the run-up), they can jump up to 15 ft (capped by Strength score and remaining movement).
**Rubric.** Full credit: cite jump rules; correctly account for run-up cost and remaining movement.

### Q44 (rules-spread) — Help on Initiative
**Q.** Can Help grant Advantage on Initiative rolls?
**A.** Initiative is a Dexterity check (p. 13). Help does apply to ability checks. But Help requires being adjacent to the helped creature with a defined trigger, and timing-wise Help happens on a turn during combat — initiative is rolled BEFORE combat starts, so there's no turn yet to take an action on. Practically, Help cannot be used during initiative rolling.
**Rubric.** Full credit: identify Initiative as a Dex check; identify the timing impossibility.

### Q45 (rules-spread) — Magic Resistance vs. Vicious Mockery
**Q.** Does Magic Resistance work against Vicious Mockery?
**A.** Yes. Vicious Mockery is a cantrip (a spell). Magic Resistance gives Advantage on saves against spells.
**Rubric.** Full credit: cantrips are spells; Magic Resistance applies.

### Q46 (rules-spread) — Ready a spell
**Q.** A Wizard Readies Fireball. Slot expended at cast or at trigger?
**A.** At cast. The Wizard casts Fireball on their turn, holds it with Concentration (per the Ready action's spell-holding rule), and releases it as a Reaction on trigger. If Concentration breaks before trigger, the spell is lost AND the slot is expended.
**Rubric.** Full credit: cite Ready; cite Concentration-hold-spell mechanic; slot expended at cast.

### Q47 (rules-spread) — Cleave order-of-attacks
**Q.** Glaive (Cleave). Miss first, hit second on a different target. Cleave triggers?
**A.** Yes. Cleave's trigger is on the *hit*; the first attack missing didn't trigger Cleave. The second attack (hit) can trigger Cleave against a creature within 5 ft of the second target, within reach. Cleave's once-per-turn limit is satisfied.
**Rubric.** Full credit: trigger on hit; once-per-turn satisfied.

### Q48 (rules-spread) — Charmed and the charmer's allies
**Q.** Can a Charmed character damage the charmer's allies?
**A.** Yes. Charmed only forbids attacking or targeting "the charmer" with damaging abilities — not the charmer's allies.
**Rubric.** Full credit: quote Charmed; clarify scope.

### Q49 (rules-spread) — Turn Undead and Magic Resistance
**Q.** A Vampire (Magic Resistance) targeted by Turn Undead?
**A.** Turn Undead is a Channel Divinity (magical but not a spell). Magic Resistance covers "spells and other magical effects." Channel Divinity is generally treated as a magical effect, so the Vampire likely gets Advantage on the Wisdom save. Some interpretations limit Magic Resistance to spells only — the SRD wording explicitly extends to "other magical effects," supporting the broader application.
**Rubric.** Full credit: identify Channel Divinity as magical; cite "other magical effects" wording; conclude likely Advantage.

### Q50 (rules-spread) — Slow mastery + Grapple
**Q.** A Slow-mastery hit AND a Grapple on the same target. Speed?
**A.** 0. Grappled imposes Speed 0 outright. Slow's −10 to Speed is irrelevant while Grappled (Speed cannot go below 0). When Grappled ends, Slow's effect (if still active) reduces base Speed by 10 ft.
**Rubric.** Full credit: identify both effects coexist; Speed cannot go below 0; effects independent.

---

## CATEGORY 2 — VERSION-SPECIFIC (Q51–75)

### Q51 (version-specific) — Surprised condition
**Q.** What happens to a Surprised creature in SRD 5.2.1?
**A.** They have Disadvantage on the Initiative roll. SRD 5.2.1 Combat / Initiative section: "Surprise. If a combatant is surprised by combat starting, that combatant has Disadvantage on their Initiative roll. For example, if an ambusher starts combat while hidden from a foe who is unaware that combat is starting, that foe is surprised."
**SRD 5.1 / 2014 answer (different).** A surprised creature could not move, take an action, or take a Reaction during the first turn of combat — effectively skipped the entire first round.
**Common wrong answers.** "They skip their first turn" (2014); "They have the Stunned condition" (false).
**Rubric.** Full credit: state SRD 5.2.1 rule; explicitly contrast with 2014.

### Q52 (version-specific) — Grappling mechanics
**Q.** How does an Unarmed Strike Grapple work?
**A.** Per SRD 5.2.1 Unarmed Strike: choose Damage, Grapple, or Shove. For Grapple: "The target must succeed on a Strength or Dexterity saving throw (it chooses which), or it has the Grappled condition. The DC for the saving throw and any escape attempts equals 8 plus your Strength modifier and Proficiency Bonus. This grapple is possible only if the target is no more than one size larger than you and if you have a hand free to grab it."
**SRD 5.1 / 2014 answer (different).** A contested Strength (Athletics) check by the attacker against the target's Strength (Athletics) or Dexterity (Acrobatics) check.
**Rubric.** Full credit: (a) save-based; (b) DC = 8 + Str + PB; (c) target chooses Str or Dex; (d) note 2014 difference.

### Q53 (version-specific) — Exhaustion
**Q.** How does Exhaustion work in SRD 5.2.1?
**A.** Cumulative levels. Each level: −2 × level on D20 Tests; −5 ft × level Speed reduction. Long Rest removes 1 level. Death at level 6.
**SRD 5.1 / 2014 answer (different).** Six discrete levels with distinct effects per level (Lv 1 = Disadvantage on ability checks; Lv 2 = Speed halved; Lv 3 = Disadvantage on attacks/saves; Lv 4 = HP max halved; Lv 5 = Speed 0; Lv 6 = death).
**One D&D playtest answer (also different — important confounder).** *Unearthed Arcana 2022: Expert Classes* (Wizards of the Coast, second One D&D playtest packet, released September 30, 2022) used 10 levels, with each level imposing −1 to all D20 Tests and to spell save DCs (no movement penalty), and death at level 11+. This is NOT the published 2024/SRD rule.
**Common wrong answers.** "10 levels with −1 per level" (the Unearthed Arcana 2022 playtest); discrete-effects-per-level (2014).
**Rubric.** Full credit: (a) −2 × level on D20 Tests; (b) −5 ft × level Speed; (c) Long Rest removes 1; (d) death at 6; (e) flag both 2014 and the One D&D playtest as confounders.

### Q54 (version-specific) — Aasimar
**Q.** Is Aasimar a playable species in SRD 5.2.1?
**A.** No. SRD 5.2.1's nine species are Dragonborn, Dwarf, Elf, Gnome, Goliath, Halfling, Human, Orc, Tiefling. Aasimar is in the 2024 PHB but excluded from the SRD. Wizards of the Coast confirmed this in their official SRD FAQ published April 22, 2025 on D&D Beyond (dndbeyond.com/srd): "SRD 5.2 includes a wide range of content from the 2024 core rulebooks, but some classes (such as the Artificer), species (like Aasimar), and monsters (including the Beholder) have been excluded. These exclusions are based on brand identity protection, licensing strategy, and intellectual property rights."
**Rubric.** Full credit: list 9 species; cite Wizards FAQ; identify Aasimar as excluded.

### Q55 (version-specific) — Artificer
**Q.** Is the Artificer in SRD 5.2.1?
**A.** No. The 12 included classes are Barbarian, Bard, Cleric, Druid, Fighter, Monk, Paladin, Ranger, Rogue, Sorcerer, Warlock, Wizard. Artificer is in the 2024 PHB but excluded per Wizards' FAQ (cited above).
**Rubric.** Full credit: list 12 classes; identify Artificer as excluded.

### Q56 (version-specific) — Cleric Domains in SRD
**Q.** Which Cleric Domains are in SRD 5.2.1?
**A.** Only the Life Domain (p. 40). The 2024 PHB has multiple Domains (Life, Light, Trickery, War, Knowledge, etc.); SRD 5.2.1 includes one Domain only.
**Rubric.** Full credit: Life Domain only; flag others as outside SRD.

### Q57 (version-specific) — Wish
**Q.** Is Wish in SRD 5.2.1?
**A.** No. Wish is in the 2024 PHB but excluded from SRD 5.2.1 (continuing its absence from SRD 5.1). Other 9th-level spells like True Polymorph, Power Word Kill, Foresight, Meteor Swarm, Time Stop, and Prismatic Wall are present.
**Rubric.** Full credit: identify Wish as excluded; mention which 9th-levels are present.

### Q58 (version-specific) — Divine Smite
**Q.** Casting time and mechanics of Divine Smite in SRD 5.2.1?
**A.** 1st-level Paladin spell. Casting Time: 1 Bonus Action, taken immediately after hitting with a Melee weapon or Unarmed Strike. Damage: 2d8 Radiant (+1d8 vs. Fiend or Undead); +1d8 per spell slot above 1st. Components: Verbal. Range: Self. Duration: Instantaneous.
**SRD 5.1 / 2014 answer (different).** Class feature (NOT a spell), no Bonus Action cost, could be triggered after any successful melee weapon attack (including OAs), used Paladin spell slots, scaled 2d8 to 5d8, could be used multiple times per turn (limited by slots), couldn't be Counterspelled.
**Common wrong answers.** "Class feature, multiple per turn" (2014); "doesn't require Concentration" — actually true in 2024, but worth confirming.
**Rubric.** Full credit: (a) it's a spell; (b) Bonus Action cost; (c) once-per-turn implicitly; (d) Verbal component (so can be Counterspelled and Silenced); (e) flag the 2014 difference.

### Q59 (version-specific) — Dazed condition
**Q.** Is Dazed a condition in SRD 5.2.1?
**A.** No. SRD 5.2.1 lists 15 conditions: Blinded, Charmed, Deafened, Exhaustion, Frightened, Grappled, Incapacitated, Invisible, Paralyzed, Petrified, Poisoned, Prone, Restrained, Stunned, Unconscious. Dazed is a 2024 PHB-introduced condition (appearing on certain class features) but is not in the SRD's condition list.
**Rubric.** Full credit: list SRD conditions; flag Dazed as outside SRD.

### Q60 (version-specific) — Counterspell
**Q.** How does Counterspell work in SRD 5.2.1?
**A.** SRD 5.2.1 Counterspell: "You attempt to interrupt a creature in the process of casting a spell. The creature makes a Constitution saving throw. On a failed save, the spell dissipates with no effect, and the action, Bonus Action, or Reaction used to cast it is wasted. If that spell was cast with a spell slot, the slot isn't expended."
**SRD 5.1 / 2014 answer (different).** Auto-counter for spells of 3rd level or lower; for higher-level, an ability check (DC 10 + spell's level). Slot was always expended on success.
**Differences.** (1) Con save by target caster, not ability check by Counterspeller; (2) slot preserved on failed save (significant for Legendary Resistance interactions); (3) much weaker against bosses with high Con saves and/or LR.
**Rubric.** Full credit: (a) Con save mechanic; (b) slot preserved; (c) flag SRD 5.1 difference.

### Q61 (version-specific) — D20 Test
**Q.** What's the umbrella term for ability checks, attack rolls, and saving throws in SRD 5.2.1?
**A.** "D20 Test." Conversion guide (Wizards): "'D20 Test' is the new umbrella term for ability checks, attack rolls, and saving throws."
**Rubric.** Full credit: identify "D20 Test."

### Q62 (version-specific) — Inspiration → Heroic Inspiration
**Q.** Is Inspiration in SRD 5.2.1?
**A.** It's been replaced by Heroic Inspiration: "If you have Heroic Inspiration, you can expend it to reroll any die immediately after rolling it, and you must use the new roll." Mechanically a reroll; the 2014/5.1 version granted Advantage instead.
**Rubric.** Full credit: name change + mechanic change (reroll vs. Advantage).

### Q63 (version-specific) — Magic action
**Q.** What's the Magic action?
**A.** SRD 5.2.1 Actions (p. 10): "Cast a spell, use a magic item, or use a magical feature." It absorbs the older "Cast a Spell" action and broadens it.
**Rubric.** Full credit: identify Magic action; identify scope.

### Q64 (version-specific) — Influence action
**Q.** What's the Influence action?
**A.** SRD 5.2.1 Actions: "Make a Charisma (Deception, Intimidation, Performance, or Persuasion) or Wisdom (Animal Handling) check to alter a creature's attitude." This is new in SRD 5.2.1.
**Rubric.** Full credit: ID as new; quote text.

### Q65 (version-specific) — Origin Feats
**Q.** Which Origin Feats are in SRD 5.2.1?
**A.** Four: **Alert, Magic Initiate, Savage Attacker, Skilled** (p. 87). The 2024 PHB has more (Crafter, Healer, Lucky, Musician, Tavern Brawler, Tough), but those are excluded from SRD 5.2.1.
**Rubric.** Full credit: list four; flag others as outside SRD.

### Q66 (version-specific) — Backgrounds
**Q.** Which backgrounds are in SRD 5.2.1?
**A.** Four: **Acolyte, Criminal, Sage, Soldier** (p. 83). The 2024 PHB has 16 backgrounds.
**Rubric.** Full credit: list four.

### Q67 (version-specific) — Two-Weapon Fighting
**Q.** How is Two-Weapon Fighting handled in SRD 5.2.1?
**A.** It's now an effect of the Light weapon property, not a separate combat rule: "When you take the Attack action on your turn and attack with a Light weapon, you can make one extra attack as a Bonus Action later on the same turn. That extra attack must be made with a different Light weapon, and you don't add your ability modifier to the extra attack's damage unless that modifier is negative." The Two-Weapon Fighting Fighting Style feat restores the ability modifier to the bonus damage. The Nick weapon mastery converts the extra attack from a Bonus Action into part of the Attack action.
**SRD 5.1 / 2014 answer (different).** A standalone Combat rule; Bonus Action by default; Fighting Style added the modifier.
**Rubric.** Full credit: (a) Light property mechanic; (b) Fighting Style restoration; (c) Nick interaction; (d) note 2014 standalone rule.

### Q68 (version-specific) — Knocking Out a Creature
**Q.** How does the "knock out" rule work?
**A.** SRD 5.2.1 (Damage and Healing, p. 17): "When you would reduce a creature to 0 Hit Points with a melee attack, you can instead reduce the creature to 1 Hit Point and give it the Unconscious condition. It then starts a Short Rest, at the end of which that condition ends on it. The condition ends early if the creature regains any Hit Points or if someone takes an action to administer first aid to it, making a successful DC 10 Wisdom (Medicine) check."
**SRD 5.1 / 2014 answer (different).** 0 HP and Unconscious; woke when healed.
**Rubric.** Full credit: (a) HP=1; (b) starts Short Rest; (c) ends on healing or Medicine check; (d) flag 2014 difference.

### Q69 (version-specific) — Crawling
**Q.** Does crawling cost extra movement?
**A.** Yes. Rules Glossary "Crawling": "While you're crawling, each foot of movement costs 1 extra foot (2 extra feet in Difficult Terrain)."
**Rubric.** Full credit: cite Crawling rule; movement cost.

### Q70 (version-specific) — Conjure Animals redesign
**Q.** Does Conjure Animals summon multiple beasts in SRD 5.2.1?
**A.** No (in 2024 PHB redesign — verify in SRD spell description). The 2024 redesign converted Conjure Animals (and the other Conjure spells) from "summon X creatures" to a single magical entity with stat-block-like properties, eliminating the DM-choice-of-stat-blocks problem from 2014. The redesigned spell aligns with the Conjure spell pattern (e.g., Conjure Minor Elementals).
**Rubric.** Full credit: identify single-entity redesign; flag if checking SRD's specific text.

### Q71 (version-specific) — Wild Magic Sorcerer
**Q.** Is Wild Magic Sorcery in SRD 5.2.1?
**A.** No. SRD 5.2.1's only Sorcerer subclass is Draconic Sorcery (p. 69). Wild Magic Sorcery is in the 2024 PHB but excluded from SRD.
**Rubric.** Full credit: identify Wild Magic as outside SRD.

### Q72 (version-specific) — Iconic monsters
**Q.** Are Beholders, Mind Flayers, Yuan-ti in SRD 5.2.1?
**A.** No — all excluded. SRD 5.2.1 monster index does NOT include Beholder, Mind Flayer (Illithid), Yuan-ti, Slaad, Githyanki, Githzerai, Kuo-toa, Modron, Displacer Beast, Umber Hulk, or Carrion Crawler. WotC FAQ: "monsters (including the Beholder) have been excluded… brand identity protection, licensing strategy, and intellectual property rights."
**Rubric.** Full credit: list multiple excluded iconic monsters; cite FAQ rationale.

### Q73 (version-specific) — Surprise vs. Invisible during initiative
**Q.** A creature is Invisible AND surprised. Initiative roll modifier?
**A.** Cancels to a straight d20. Invisible (Conditions): "Surprise. If you're Invisible when you roll Initiative, you have Advantage on the roll." Surprised creature: Disadvantage on Initiative. Advantage + Disadvantage = neither.
**Rubric.** Full credit: identify both effects; cite no-stacking rule.

### Q74 (version-specific) — Find Familiar
**Q.** Is Find Familiar in SRD 5.2.1?
**A.** Yes (verify Wizard spell list). Notable 2024 features in SRD: telepathic communication within 100 ft; familiar shares your initiative or rolls its own; familiar takes a Reaction to deliver touch spells.
**Rubric.** Full credit: spell present; note key 2024 changes.

### Q75 (version-specific) — Use an Object → Utilize
**Q.** What's the new name for "Use an Object"?
**A.** "Utilize" — Actions list (p. 10): "Utilize. Use a nonmagical object." Same intent, new name.
**Rubric.** Full credit: identify rename.

---

## CATEGORY 3 — COMMON TABLE QUESTIONS (Q76–90)

### Q76 (common) — Cover
**A.** Three degrees: Half (+2 AC and Dex saves; from a creature OR object covering at least half of the target), Three-Quarters (+5 AC and Dex saves; from an object covering at least three-quarters), Total (cannot be targeted directly). Only the most protective applies; degrees don't stack. From SRD 5.2.1 Cover (p. 15): "If a target is behind multiple sources of cover, only the most protective degree of cover applies; the degrees aren't added together."
**Rubric.** Full credit: list all three with their grants; non-stacking; creatures only ever provide Half Cover.

### Q77 (common) — Move through ally's space
**A.** Yes; the ally's space is NOT Difficult Terrain. SRD 5.2.1 Movement (p. 14): "During your move, you can pass through the space of an ally, a creature that has the Incapacitated condition, a Tiny creature, or a creature that is two sizes larger or smaller than you. Another creature's space is Difficult Terrain for you unless that creature is Tiny or your ally."
**Rubric.** Full credit: cite passage; identify ally carve-out.

### Q78 (common) — Reactions
**A.** Reactions (p. 10): "A Reaction is an instant response to a trigger of some kind, which can occur on your turn or on someone else's." One per round; resets at start of your next turn. Common Reactions: Opportunity Attack, Shield, Counterspell, Reactive cast spells, the Ready action's release.
**Rubric.** Full credit: definition; one-per-round; examples.

### Q79 (common) — Ready action
**A.** Ready (Actions, p. 10): "Prepare to take an action in response to a trigger you define." On trigger, use your Reaction to take the readied action. For spells, you must hold the spell with Concentration; if Concentration breaks, the spell is lost (slot expended). Bonus Actions and Reactions cannot be readied.
**Rubric.** Full credit: trigger and Reaction; Concentration for spells; slot expended at cast.

### Q80 (common) — Death Saving Throws
**A.** Per SRD 5.2.1 (Damage and Healing, p. 17–18): "Whenever you start your turn with 0 Hit Points, you must make a Death Saving Throw… Roll 1d20. If the roll is 10 or higher, you succeed. Otherwise, you fail. On your third success, you become Stable. On your third failure, you die. When you roll a 1 on the d20 for a Death Saving Throw, you suffer two failures. If you roll a 20 on the d20, you regain 1 Hit Point. If you take any damage while you have 0 Hit Points, you suffer a Death Saving Throw failure. If the damage is from a Critical Hit, you suffer two failures instead. If the damage equals or exceeds your Hit Point maximum, you die."
**Rubric.** Full credit: 10+ to succeed; 3-success Stable; 3-fail death; 1=2 failures; 20=+1 HP; crit=2 failures; massive damage = death.

### Q81 (common) — Difficult Terrain
**A.** Movement, p. 14: "Every foot of movement in Difficult Terrain costs 1 extra foot, even if multiple things in a space count as Difficult Terrain." Non-stacking.
**Rubric.** Full credit: cost-doubling; non-stacking.

### Q82 (common) — One spell per turn
**A.** SRD 5.2.1 streamlines the 2014 "Bonus-Action spell + cantrip" rule. The general rule is one spell per turn. Reactions (cast on others' turns) are unaffected. Verify exact wording in SRD 5.2.1's Casting Spells section, p. 104+.
**Rubric.** Full credit: identify one-per-turn; flag Reaction exception.

### Q83 (common) — Long Rest
**A.** 8-hour period; up to 2 hours of light activity allowed during. Restores all HP and half spent Hit Dice (round down). One per 24-hour period.
**Rubric.** Full credit: 8 hours; once per day; HP fully restored; half Hit Dice.

### Q84 (common) — Short Rest
**A.** Minimum 1 hour of light activity. Spending Hit Dice can restore HP (1 die + Con mod per die). Some class features recharge.
**Rubric.** Full credit: 1 hour; Hit Dice spending.

### Q85 (common) — Concentration
**A.** Some spells require Concentration. Casting another Concentration spell ends the current. Incapacitation ends it. On taking damage: Con save, DC = max(10, half damage taken). One concurrent Concentration spell maximum.
**Rubric.** Full credit: all four conditions; correct DC formula.

### Q86 (common) — Hide action
**A.** SRD 5.2.1 Hide: a Dexterity (Stealth) check, DC 15 (per the Rules Glossary's Hide entry). Success grants the Invisible condition. Prerequisites: must be in Lightly Obscured space or behind cover; cannot be observed.
**Rubric.** Full credit: DC 15; Invisible on success; cover/obscurity prerequisite.

### Q87 (common) — Initiative
**A.** Combat (p. 13): "Every participant rolls Initiative; they make a Dexterity check that determines their place in the Initiative order." Tied: GM decides between monsters; players among themselves; GM if mixed.
**Rubric.** Full credit: Dex check; tiebreaking.

### Q88 (common) — Critical Hits
**A.** Damage and Healing (p. 16): "When you score a Critical Hit, you deal extra damage. Roll the attack's damage dice twice, add them together, and add any relevant modifiers as normal." Modifiers (e.g., Strength bonus) are NOT doubled. Bonus dice (e.g., Sneak Attack) ARE doubled. Natural 20 is always a hit and a Critical Hit. Natural 1 always misses.
**Rubric.** Full credit: double dice (not modifiers); natural 20 = auto-hit + crit; bonus dice double.

### Q89 (common) — Bloodied
**A.** Damage and Healing (p. 16): "If you have half your Hit Points or fewer, you're Bloodied, which has no game effect on its own but which might trigger other game effects." A status flag, not a condition.
**Rubric.** Full credit: ≤ half max HP; no inherent effect.

### Q90 (common) — Dash
**A.** Actions (p. 9): "For the rest of the turn, give yourself extra movement equal to your Speed."
**Rubric.** Full credit: extra movement = Speed; rest of turn.

---

## CATEGORY 4 — CONTENTIOUS / INTERPRETIVE (Q91–100)

For these, the agent should NOT take sides. The rubric rewards recognizing and presenting the ambiguity, citing relevant SRD 5.2.1 text.

### Q91 (contentious) — Familiar Help in combat
**Q.** Does a familiar's Help action grant Advantage on an ally's attack in combat?
**Reading 1 (RAW yes).** Find Familiar's Combat clause says the familiar can take actions other than Attack; Help is an action. Help requires being within 5 ft of the target; if the familiar gets adjacent to the enemy, RAW it grants Advantage to the next ally's attack.
**Reading 2 (skeptical).** Help describes "feinting, distracting, or in some other way teaming up." A Tiny familiar may not credibly do that; some DMs deny based on narrative plausibility.
**Reading 3 (timing).** When does the helper's adjacency need to hold? Some say only at the moment of helping; others require adjacency until the ally attacks. SRD 5.2.1 doesn't explicitly resolve.
**Rubric.** Full credit: present multiple readings; cite Find Familiar's Combat clause and Help's text; do NOT pick a side.

### Q92 (contentious) — What counts as "casting a spell"
**Q.** Does activating a Wand of Fireballs trigger Counterspell?
**Ambiguity.** Counterspell requires "casting a spell with Verbal, Somatic, or Material components." Magic items: some are flavored as the user "casting a spell" (with the V/S/M from the item), others are spell-like effects without components attributed to the user. Innate spellcasting (some monsters) sometimes specifies "no material components" or "no components" — those wouldn't trigger Counterspell. The "Magic action" use of a "magical feature" is also ambiguous: a feature that creates a spell effect may or may not count as casting a spell.
**Rubric.** Full credit: present multiple readings; cite Counterspell's V/S/M trigger language; do not take a side.

### Q93 (contentious) — Reaction-cast spells and the one-spell-per-turn rule
**Q.** Can you cast a leveled spell action *and* a Reaction-cast spell (e.g., Shield) on your own turn?
**Ambiguity.** "One spell per turn" — on whose turn? If a Reaction is triggered on your own turn (e.g., you provoke an OA during your move and Shield in response), it's arguably "your turn." Most readings: Reactions are exempt from the one-spell-per-turn rule. SRD 5.2.1 doesn't explicitly clarify edge cases.
**Rubric.** Full credit: present competing readings.

### Q94 (contentious) — Hide → Invisible → multiple attacks
**Q.** Does Hide-acquired Invisibility grant Advantage on every attack until something specifically reveals you, or just the next one?
**Reading 1.** "If you are hidden when you make an attack roll, you give away your location when the attack hits or misses" — single attack ends concealment. Advantage applies to that one attack.
**Reading 2.** Invisible condition persists until the listed end conditions; multiple attacks remain Advantaged until then.
**Rubric.** Full credit: present both readings.

### Q95 (contentious) — Forced movement of a grappler
**Q.** A grappler is pushed away by Thunderwave. Does the grappled creature come along, or stay?
**Reading 1.** The grappled creature stays; the grapple ends as range is exceeded.
**Reading 2.** The grapple is a tether; both move together (the grappler "drags" the grappled by force of grip during the forced movement).
**SRD 5.2.1 doesn't fully resolve.** Many tables treat forced movement of the grappler as ending the grapple via range exceedance; others rule the grappled is dragged.
**Rubric.** Full credit: present competing readings; cite Grappled range-exceedance clause.

### Q96 (contentious) — "Magical effects" scope for Magic Resistance
**Q.** What counts as a "magical effect" beyond spells?
**Ambiguity.** "Spells and other magical effects" is broader than "spells" but the SRD doesn't enumerate. Magic-item effects, monster traits flagged "magical," Channel Divinity, Wild Shape, etc. — different DMs draw different lines. The SRD's broader phrasing supports inclusive readings, but specific edge cases lack clarity.
**Rubric.** Full credit: present the breadth; note edge cases.

### Q97 (contentious) — Topple on legless creatures
**Q.** Can a snake or ooze be made Prone via Topple?
**Ambiguity.** Topple imposes the Prone condition on a failed Con save. Prone (Conditions) describes restriction on movement and combat consequences, but doesn't require legs as a prerequisite. RAW: legless creatures can be Prone. Some DMs rule narrative immunity for slithering/oozing/swimming creatures. SRD 5.2.1 has no explicit exemption.
**Rubric.** Full credit: cite Topple + Prone; note no explicit exemption; flag DM discretion.

### Q98 (contentious) — Bloodied trigger timing
**Q.** When does Bloodied "fire"?
**Ambiguity.** Bloodied is a status flag. Whether it triggers exactly when HP reaches half (during damage application) or only on the next observation by a feature that keys off it, the SRD doesn't specify timing.
**Rubric.** Full credit: identify timing ambiguity.

### Q99 (contentious) — Familiar's senses for spell targeting
**Q.** Can a Wizard target a creature with a sight-required spell while using "see through familiar's eyes"?
**Reading 1.** Yes — the Wizard literally sees the target via the familiar.
**Reading 2.** No — spells require the *caster's own* senses, not borrowed ones.
**Most rulings.** Yes (consistent with prior official rulings), but SRD 5.2.1 doesn't explicitly resolve.
**Rubric.** Full credit: present both readings.

### Q100 (contentious) — Standing from Prone provoking OAs
**Q.** Standing up costs half Speed (movement). Does it provoke OAs?
**Reading 1.** Standing doesn't change your square; you don't "leave" any reach; no OA.
**Reading 2.** Standing is movement, and any movement may technically pass through enemy reach in tight spaces; some DMs trigger OAs.
**Most rulings.** No OA from standing in place. SRD 5.2.1 doesn't explicitly resolve.
**Rubric.** Full credit: present both readings; cite Prone movement options.

---

# Recommendations

1. **Use the version-specific category as your highest-signal subset.** Q51–75 are the most likely to expose foundation models defaulting to 2014 rules. If an agent fails Q51, Q52, Q53, Q58, Q60, or Q68 by giving the 2014 answer confidently, that's a strong indicator of inadequate retrieval grounding.
2. **For each version-specific question, run two evaluation passes.** First with the question phrased neutrally ("How does grappling work?"), and second with explicit version anchoring ("In SRD 5.2.1 specifically, how does grappling work?"). The delta between the two passes measures whether the agent can be primed toward correct version vs. whether it knows by default.
3. **Score contentious questions binarily on bias.** Any contentious question where the agent firmly takes one side without acknowledging the alternative reading should fail the rubric, regardless of which side it takes.
4. **Use the SRD-exclusion questions (Q40, Q54, Q55, Q56, Q57, Q59, Q65, Q66, Q71, Q72) as a "scope filter" check.** If the agent confidently invokes excluded content (Aasimar, Artificer, Wish, Wild Magic, Beholder, etc.) without flagging it as outside SRD 5.2.1, the agent is failing at scope discipline — a critical quality for an SRD-only legal-compliance use case.
5. **Threshold for production readiness.** I'd suggest these benchmarks: ≥ 90% on common questions (Q76–90); ≥ 85% on rules-spread (Q1–50); ≥ 80% on version-specific (Q51–75); ≥ 70% on contentious (Q91–100, scored on ambiguity-acknowledgment, not "correct" answer).
6. **Re-evaluate after errata.** If Wizards releases SRD 5.2.2 or 5.3, several questions (especially version-specific) will need re-grading against the new authoritative text. Treat the corpus as version-locked to SRD 5.2.1 (April 22, 2025 / May 1, 2025 update).

# Caveats

1. **Page numbers are approximate** in some cases — the corpus references the SRD 5.2.1 PDF's table of contents and verified passages, but the agent under test should be able to locate specific passages by section header (e.g., "Conditions," "Combat / Initiative," "Mastery Properties") rather than relying on page numbers alone.
2. **Some specific SRD 5.2.1 text was not 100% verified verbatim** in this corpus's drafting — particularly the precise wording of Casting Spells / Concentration sections and the exact text of Hunter's Mark and Find Familiar in SRD 5.2.1 vs. the 2024 PHB. Reviewers should spot-check questions Q39, Q70, Q74, Q82, and Q85 against the SRD 5.2.1 PDF directly before using as grading gold standard.
3. **Some "common wrong answers" reflect 2014 rules.** Foundation models trained primarily on the 2014 5e corpus will be especially likely to give those answers; this is intentional for the test's purpose.
4. **Contentious questions intentionally lack a "correct" answer.** Grading them requires a rubric scorer who recognizes valid presentations of multiple readings. Avoid auto-grading these against a single answer key.
5. **The Exhaustion confounder is documented:** the *Unearthed Arcana 2022: Expert Classes* playtest packet (released September 30, 2022, the second One D&D playtest) used 10 levels with −1/level, no movement penalty, and death at 11+. This is distinct from both the 2014 SRD 5.1 (6 levels, distinct effects per level) and the published 2024 PHB / SRD 5.2.1 (6 levels, −2 × level / −5 ft × level / death at 6). Foundation models trained on playtest documents may give the 10-level answer; that's a wrong answer per SRD 5.2.1.
6. **The Aasimar/Artificer exclusion is permanent under CC-BY-4.0 once published.** Per Wizards' FAQ: "Once a document is published under the Creative Commons Attribution 4.0 International License (CC-BY-4.0), it is permanently available under those terms. Wizards of the Coast cannot revoke or alter SRD 5.2 or remove it from Creative Commons." So the exclusions are a stable feature of SRD 5.2.1, but Wizards retains the right to add content in future SRD 5.3 etc. Update the corpus when new SRDs ship.