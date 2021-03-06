import {RandomTeams, TeamData} from '../../random-teams';
import {PRNG, PRNGSeed} from '../../../sim/prng';
import {Utils} from '../../../lib';
import {toID} from '../../../sim/dex';

export class RandomGen7Teams extends RandomTeams {
	constructor(format: Format | string, prng: PRNG | PRNGSeed | null) {
		super(format, prng);
	}

	randomSet(
		species: string | Species,
		teamDetails: RandomTeamsTypes.TeamDetails = {},
		isLead = false,
		isDoubles = false
	): RandomTeamsTypes.RandomSet {
		species = this.dex.getSpecies(species);
		let forme = species.name;

		if (typeof species.battleOnly === 'string') {
			// Only change the forme. The species has custom moves, and may have different typing and requirements.
			forme = species.battleOnly;
		}
		if (species.cosmeticFormes) {
			forme = this.sample([species.name].concat(species.cosmeticFormes));
		}

		const randMoves = !isDoubles ?
			species.randomBattleMoves :
			(species.randomDoubleBattleMoves || species.randomBattleMoves);
		const movePool = (randMoves || Object.keys(Dex.getLearnsetData(species.id).learnset!)).slice();
		const rejectedPool = [];
		const moves: string[] = [];
		let ability = '';
		let item = '';
		const evs = {
			hp: 85, atk: 85, def: 85, spa: 85, spd: 85, spe: 85,
		};
		const ivs = {
			hp: 31, atk: 31, def: 31, spa: 31, spd: 31, spe: 31,
		};
		const hasType: {[k: string]: true} = {};
		hasType[species.types[0]] = true;
		if (species.types[1]) {
			hasType[species.types[1]] = true;
		}
		const hasAbility: {[k: string]: true} = {};
		hasAbility[species.abilities[0]] = true;
		if (species.abilities[1]) {
			hasAbility[species.abilities[1]] = true;
		}
		if (species.abilities['H']) {
			hasAbility[species.abilities['H']] = true;
		}
		let availableHP = 0;
		for (const moveid of movePool) {
			if (moveid.startsWith('hiddenpower')) availableHP++;
		}

		// These moves can be used even if we aren't setting up to use them:
		const SetupException = ['closecombat', 'diamondstorm', 'extremespeed', 'superpower', 'clangingscales'];

		let hasMove: {[k: string]: boolean} = {};
		let counter;

		do {
			// Keep track of all moves we have:
			hasMove = {};
			for (const moveid of moves) {
				if (moveid.startsWith('hiddenpower')) {
					hasMove['hiddenpower'] = true;
				} else {
					hasMove[moveid] = true;
				}
			}

			// Choose next 4 moves from learnset/viable moves and add them to moves list:
			while (moves.length < 4 && movePool.length) {
				const moveid = this.sampleNoReplace(movePool);
				if (moveid.startsWith('hiddenpower')) {
					availableHP--;
					if (hasMove['hiddenpower']) continue;
					hasMove['hiddenpower'] = true;
				} else {
					hasMove[moveid] = true;
				}
				moves.push(moveid);
			}
			while (moves.length < 4 && rejectedPool.length) {
				const moveid = this.sampleNoReplace(rejectedPool);
				hasMove[moveid] = true;
				moves.push(moveid);
			}

			counter = this.queryMoves(moves, hasType, hasAbility, movePool);

			// Iterate through the moves again, this time to cull them:
			for (const [k, moveId] of moves.entries()) {
				const move = this.dex.getMove(moveId);
				const moveid = move.id;
				let rejected = false;
				let isSetup = false;

				switch (moveid) {
				// Not very useful without their supporting moves
				case 'clangingscales': case 'electricterrain': case 'happyhour': case 'holdhands':
					if (teamDetails.zMove || hasMove['rest'] && hasMove['sleeptalk']) rejected = true;
					if (moveid === 'happyhour' || moveid === 'holdhands') isSetup = true;
					break;
				case 'cottonguard': case 'defendorder':
					if (!counter['recovery'] && !hasMove['rest']) rejected = true;
					break;
				case 'bounce': case 'dig': case 'fly':
					if (teamDetails.zMove || counter.setupType !== 'Physical') rejected = true;
					break;
				case 'focuspunch':
					if (!hasMove['substitute'] || counter.damagingMoves.length < 2) rejected = true;
					break;
				case 'icebeam':
					if (hasAbility['Tinted Lens'] && !!counter['Status']) rejected = true;
					break;
				case 'perishsong':
					if (!hasMove['protect']) rejected = true;
					break;
				case 'reflect':
					if (!hasMove['calmmind'] && !hasMove['lightscreen']) rejected = true;
					if (movePool.length > 1) {
						const screen = movePool.indexOf('lightscreen');
						if (screen >= 0) this.fastPop(movePool, screen);
					}
					break;
				case 'rest':
					if (movePool.includes('sleeptalk')) rejected = true;
					break;
				case 'sleeptalk':
					if (!hasMove['rest']) rejected = true;
					if (movePool.length > 1) {
						const rest = movePool.indexOf('rest');
						if (rest >= 0) this.fastPop(movePool, rest);
					}
					break;
				case 'storedpower':
					if (!counter.setupType) rejected = true;
					break;
				case 'switcheroo': case 'trick':
					if (counter.Physical + counter.Special < 3 || ['electroweb', 'snarl', 'suckerpunch'].some(m => hasMove[m])) {
						rejected = true;
					}
					break;

				// Set up once and only if we have the moves for it
				case 'bellydrum': case 'bulkup': case 'coil': case 'curse': case 'dragondance': case 'honeclaws': case 'swordsdance':
					if (counter.setupType !== 'Physical' || counter['physicalsetup'] > 1) rejected = true;
					if (counter.Physical + counter['physicalpool'] < 2 && (!hasMove['rest'] || !hasMove['sleeptalk'])) rejected = true;
					if (moveid === 'bellydrum' && !hasAbility['Unburden'] && !counter['priority']) rejected = true;
					if (moveid === 'bulkup' && hasMove['rest'] && hasMove['sleeptalk']) rejected = true;
					isSetup = true;
					break;
				case 'calmmind': case 'geomancy': case 'nastyplot': case 'quiverdance': case 'tailglow':
					if (counter.setupType !== 'Special' || counter['specialsetup'] > 1) rejected = true;
					if (counter.Special + counter['specialpool'] < 2 && (!hasMove['rest'] || !hasMove['sleeptalk'])) rejected = true;
					if (hasType['Dark'] && hasMove['darkpulse']) {
						counter.setupType = 'Special';
						rejected = false;
					}
					isSetup = true;
					break;
				case 'growth': case 'shellsmash': case 'workup':
					if (counter.setupType !== 'Mixed' || counter['mixedsetup'] > 1) rejected = true;
					if (counter.damagingMoves.length + counter['physicalpool'] + counter['specialpool'] < 2) rejected = true;
					if (moveid === 'growth' && !hasMove['sunnyday']) rejected = true;
					isSetup = true;
					break;
				case 'agility': case 'autotomize': case 'rockpolish': case 'shiftgear':
					if (counter.damagingMoves.length < 2 || hasMove['rest'] && hasMove['sleeptalk']) rejected = true;
					if (!counter.setupType) isSetup = true;
					break;
				case 'flamecharge':
					if (counter.damagingMoves.length < 3 && !counter.setupType) rejected = true;
					if (hasMove['dracometeor'] || hasMove['overheat']) rejected = true;
					break;

				// Bad after setup
				case 'circlethrow': case 'dragontail':
					if (
						counter.setupType &&
						((!hasMove['rest'] && !hasMove['sleeptalk']) || hasMove['stormthrow'])
					) rejected = true;
					if (
						counter['speedsetup'] ||
						['encore', 'raindance', 'roar', 'trickroom', 'whirlwind'].some(m => hasMove[m])
					) rejected = true;
					if (
						(counter[move.type] > 1 && counter.Status > 1) ||
						hasAbility['Sheer Force'] &&
						!!counter['sheerforce']
					) rejected = true;
					if (isDoubles && hasMove['superpower']) rejected = true;
					break;
				case 'defog':
					if (counter.setupType || hasMove['spikes'] || hasMove['stealthrock'] || teamDetails.defog) rejected = true;
					break;
				case 'fakeout': case 'tailwind':
					if (counter.setupType || ['substitute', 'switcheroo', 'trick'].some(m => hasMove[m])) rejected = true;
					break;
				case 'foulplay':
					if (
						counter.setupType || counter['speedsetup'] || counter['Dark'] > 2 ||
						hasMove['clearsmog'] ||
						(hasMove['rest'] && hasMove['sleeptalk'])
					) rejected = true;
					if (counter.damagingMoves.length - 1 === counter['priority']) rejected = true;
					break;
				case 'haze': case 'spikes':
					if (counter.setupType || !!counter['speedsetup'] || hasMove['trickroom']) rejected = true;
					break;
				case 'healbell': case 'technoblast':
					if (counter['speedsetup']) rejected = true;
					break;
				case 'healingwish': case 'memento':
					if (counter.setupType || !!counter['recovery'] || hasMove['substitute']) rejected = true;
					break;
				case 'helpinghand':
					if (counter.setupType) rejected = true;
					break;
				case 'icywind': case 'stringshot':
					if (!!counter['speedsetup'] || hasMove['trickroom']) rejected = true;
					break;
				case 'leechseed': case 'roar': case 'whirlwind':
					if (counter.setupType || !!counter['speedsetup'] || hasMove['dragontail']) rejected = true;
					if (isDoubles && (movePool.includes('protect') || movePool.includes('spikyshield'))) rejected = true;
					break;
				case 'protect':
					if (counter.setupType && !hasMove['wish'] && !isDoubles) rejected = true;
					if (!!counter['speedsetup'] || hasMove['rest'] || hasMove['lightscreen'] && hasMove['reflect']) rejected = true;
					if (isDoubles && (
						hasMove['fakeout'] ||
						(hasMove['tailwind'] && hasMove['roost']) ||
						movePool.includes('bellydrum') ||
						movePool.includes('shellsmash')
					)) rejected = true;
					break;
				case 'pursuit':
					if (
						counter.setupType || counter.Status > 1 || counter['Dark'] > 2 ||
						(hasMove['knockoff'] && !hasType['Dark'])
					) rejected = true;
					break;
				case 'rapidspin':
					if (counter.setupType || teamDetails.rapidSpin) rejected = true;
					break;
				case 'reversal':
					if (hasMove['substitute'] && teamDetails.zMove) rejected = true;
					break;
				case 'seismictoss': case 'superfang':
					if (!hasAbility['Parental Bond'] && (counter.damagingMoves.length > 1 || counter.setupType)) rejected = true;
					break;
				case 'stealthrock':
					if (
						counter.setupType || counter['speedsetup'] ||
						['rest', 'substitute', 'trickroom'].some(m => hasMove[m]) ||
						teamDetails.stealthRock
					) rejected = true;
					break;
				case 'stickyweb':
					if (teamDetails.stickyWeb) rejected = true;
					break;
				case 'toxicspikes':
					if (counter.setupType || teamDetails.toxicSpikes) rejected = true;
					break;
				case 'trickroom':
					if (counter.setupType || !!counter['speedsetup'] || counter.damagingMoves.length < 2) rejected = true;
					if (hasMove['lightscreen'] || hasMove['reflect']) rejected = true;
					break;
				case 'uturn':
					if (counter.setupType || counter['speedsetup'] || (
						hasType['Bug'] &&
						counter.stab < 2 && counter.damagingMoves.length > 2 &&
						!hasAbility['Adaptability'] && !hasAbility['Download']
					)) rejected = true;
					if ((hasAbility['Speed Boost'] && hasMove['protect']) || (hasAbility['Protean'] && counter.Status > 2)) rejected = true;
					break;
				case 'voltswitch':
					if (
						counter.setupType || counter['speedsetup'] ||
						['electricterrain', 'raindance', 'uturn'].some(m => hasMove[m])
					) rejected = true;
					break;

				// Bit redundant to have both
				// Attacks:
				case 'bugbite': case 'bugbuzz': case 'infestation': case 'signalbeam':
					if (hasMove['uturn'] && !counter.setupType && !hasAbility['Tinted Lens']) rejected = true;
					break;
				case 'darkestlariat': case 'nightslash':
					if (hasMove['knockoff'] || hasMove['pursuit']) rejected = true;
					break;
				case 'darkpulse':
					if (['crunch', 'knockoff', 'hyperspacefury'].some(m => hasMove[m]) && counter.setupType !== 'Special') rejected = true;
					break;
				case 'suckerpunch':
					if (counter.damagingMoves.length < 2 || hasMove['glare'] || !hasType['Dark'] && counter['Dark'] > 1) rejected = true;
					break;
				case 'dracometeor':
					if (hasMove['rest'] && hasMove['sleeptalk']) rejected = true;
					break;
				case 'dragonpulse': case 'spacialrend':
					if (hasMove['dracometeor'] || hasMove['outrage'] || (hasMove['dragontail'] && !counter.setupType)) rejected = true;
					break;
				case 'outrage':
					if (hasMove['dragonclaw'] || hasMove['dracometeor'] && counter.damagingMoves.length < 3) rejected = true;
					if (hasMove['clangingscales'] && !teamDetails.zMove) rejected = true;
					break;
				case 'thunderbolt':
					if (hasMove['discharge'] || (hasMove['voltswitch'] && hasMove['wildcharge'])) rejected = true;
					break;
				case 'moonblast':
					if (isDoubles && hasMove['dazzlinggleam']) rejected = true;
					break;
				case 'aurasphere': case 'focusblast':
					if ((hasMove['closecombat'] || hasMove['superpower']) && counter.setupType !== 'Special') rejected = true;
					if (hasMove['rest'] && hasMove['sleeptalk']) rejected = true;
					break;
				case 'drainpunch':
					if (!hasMove['bulkup'] && (hasMove['closecombat'] || hasMove['highjumpkick'])) rejected = true;
					if ((hasMove['focusblast'] || hasMove['superpower']) && counter.setupType !== 'Physical') rejected = true;
					break;
				case 'closecombat': case 'highjumpkick':
					if (counter.setupType === 'Special' && ['aurasphere', 'focusblast'].some(m => hasMove[m] || movePool.includes(m))) {
						rejected = true;
					}
					if (hasMove['bulkup'] && hasMove['drainpunch']) rejected = true;
					break;
				case 'dynamicpunch': case 'vacuumwave':
					if ((hasMove['closecombat'] || hasMove['facade']) && counter.setupType !== 'Special') rejected = true;
					break;
				case 'stormthrow':
					if (hasMove['circlethrow'] && hasMove['rest'] && hasMove['sleeptalk']) rejected = true;
					break;
				case 'superpower':
					if (counter['Fighting'] > 1 && counter.setupType) rejected = true;
					if (hasMove['rest'] && hasMove['sleeptalk'] && !hasAbility['Contrary']) rejected = true;
					if (hasAbility['Contrary']) isSetup = true;
					break;
				case 'fierydance': case 'heatwave':
					if (hasMove['fireblast'] && (!!counter.Status || isDoubles)) rejected = true;
					break;
				case 'firefang': case 'firepunch': case 'flamethrower':
					if (['blazekick', 'heatwave', 'overheat'].some(m => hasMove[m])) rejected = true;
					if ((hasMove['fireblast'] || hasMove['lavaplume']) && counter.setupType !== 'Physical') rejected = true;
					break;
				case 'fireblast': case 'magmastorm':
					if (hasMove['flareblitz'] && counter.setupType !== 'Special') rejected = true;
					if (hasMove['lavaplume'] && !counter.setupType && !counter['speedsetup']) rejected = true;
					break;
				case 'lavaplume':
					if (hasMove['firepunch'] || hasMove['fireblast'] && (counter.setupType || !!counter['speedsetup'])) rejected = true;
					break;
				case 'overheat':
					if (['fireblast', 'flareblitz', 'lavaplume'].some(m => hasMove[m])) rejected = true;
					break;
				case 'hurricane':
					if (hasMove['bravebird'] || hasMove['airslash'] && !!counter.Status) rejected = true;
					break;
				case 'hex':
					if (!hasMove['thunderwave'] && !hasMove['willowisp']) rejected = true;
					break;
				case 'shadowball':
					if (hasMove['darkpulse'] || hasMove['hex'] && hasMove['willowisp']) rejected = true;
					break;
				case 'shadowclaw':
					if (hasMove['shadowforce'] || hasMove['shadowsneak']) rejected = true;
					if (hasMove['shadowball'] && counter.setupType !== 'Physical') rejected = true;
					break;
				case 'shadowsneak':
					if (hasType['Ghost'] && species.types.length > 1 && counter.stab < 2) rejected = true;
					if (hasMove['trick'] || hasMove['rest'] && hasMove['sleeptalk']) rejected = true;
					break;
				case 'gigadrain':
					if (hasMove['petaldance'] || hasMove['powerwhip'] || (hasMove['seedbomb'] && !isDoubles)) rejected = true;
					if (hasMove['leafstorm'] && counter.Special < 4 && !counter.setupType && !hasMove['trickroom']) rejected = true;
					break;
				case 'leafblade': case 'woodhammer':
					if (hasMove['gigadrain'] && counter.setupType !== 'Physical') rejected = true;
					if (hasMove['hornleech'] && counter.setupType) rejected = true;
					break;
				case 'leafstorm':
					if (hasMove['trickroom'] || counter['Grass'] > 1 && counter.setupType) rejected = true;
					if (isDoubles && hasMove['energyball']) rejected = true;
					break;
				case 'seedbomb':
					if (hasMove['leafstorm'] || isDoubles && hasMove['gigadrain']) rejected = true;
					break;
				case 'solarbeam':
					if ((!hasAbility['Drought'] && !hasMove['sunnyday']) || hasMove['gigadrain'] || hasMove['leafstorm']) rejected = true;
					break;
				case 'bonemerang': case 'precipiceblades':
					if (hasMove['earthquake']) rejected = true;
					break;
				case 'earthpower':
					if (hasMove['earthquake'] && counter.setupType !== 'Special') rejected = true;
					break;
				case 'earthquake':
					if (isDoubles && hasMove['highhorsepower']) rejected = true;
					break;
				case 'freezedry':
					if (hasMove['icebeam'] || hasMove['icywind'] || counter.stab < 2) rejected = true;
					break;
				case 'bodyslam': case 'return':
					if (hasMove['doubleedge'] || hasMove['glare'] && hasMove['headbutt']) rejected = true;
					if (moveid === 'return' && hasMove['bodyslam']) rejected = true;
					break;
				case 'endeavor':
					if (!isLead && !hasAbility['Defeatist']) rejected = true;
					break;
				case 'explosion':
					if (counter.setupType || hasMove['wish'] || hasAbility['Refrigerate'] && hasMove['freezedry']) rejected = true;
					break;
				case 'extremespeed': case 'skyattack':
					if (hasMove['substitute'] || counter.setupType !== 'Physical' && hasMove['vacuumwave']) rejected = true;
					break;
				case 'facade':
					if (hasMove['bulkup'] || hasMove['rest'] && hasMove['sleeptalk']) rejected = true;
					break;
				case 'hiddenpower':
					if (hasMove['rest'] || !counter.stab && counter.damagingMoves.length < 2) rejected = true;
					break;
				case 'hypervoice':
					if (hasMove['blizzard']) rejected = true;
					break;
				case 'judgment':
					if (counter.setupType !== 'Special' && counter.stab > 1) rejected = true;
					break;
				case 'quickattack':
					if (!!counter['speedsetup'] || hasType['Rock'] && !!counter.Status) rejected = true;
					if (hasMove['feint'] || hasType['Normal'] && !counter.stab) rejected = true;
					break;
				case 'weatherball':
					if (!hasMove['raindance'] && !hasMove['sunnyday']) rejected = true;
					break;
				case 'poisonjab':
					if (hasMove['gunkshot']) rejected = true;
					break;
				case 'acidspray': case 'sludgewave':
					if (hasMove['poisonjab'] || hasMove['sludgebomb']) rejected = true;
					break;
				case 'psychic':
					if (hasMove['psyshock']) rejected = true;
					break;
				case 'psychocut': case 'zenheadbutt':
					if ((hasMove['psychic'] || hasMove['psyshock']) && counter.setupType !== 'Physical') rejected = true;
					if (hasAbility['Contrary'] && !counter.setupType && !!counter['physicalpool']) rejected = true;
					break;
				case 'psyshock':
					const psychic = movePool.indexOf('psychic');
					if (psychic >= 0) this.fastPop(movePool, psychic);
					break;
				case 'headsmash':
					if (hasMove['stoneedge'] || isDoubles && hasMove['rockslide']) rejected = true;
					break;
				case 'rockblast': case 'rockslide':
					if ((hasMove['headsmash'] || hasMove['stoneedge']) && !isDoubles) rejected = true;
					break;
				case 'stoneedge':
					if (hasMove['rockslide'] || hasAbility['Guts'] && !hasMove['dynamicpunch']) rejected = true;
					if (isDoubles && hasMove['rockslide']) rejected = true;
					break;
				case 'bulletpunch':
					if (hasType['Steel'] && counter.stab < 2 && !hasAbility['Technician']) rejected = true;
					break;
				case 'flashcannon':
					if ((hasMove['ironhead'] || hasMove['meteormash']) && counter.setupType !== 'Special') rejected = true;
					break;
				case 'hydropump':
					if (hasMove['liquidation'] || hasMove['waterfall'] || (hasMove['rest'] && hasMove['sleeptalk'])) rejected = true;
					if (hasMove['scald'] && (
						(counter.Special < 4 && !hasMove['uturn']) ||
						(species.types.length > 1 && counter.stab < 3)
					)) rejected = true;
					break;
				case 'muddywater':
					if (isDoubles && (hasMove['scald'] || hasMove['hydropump'])) rejected = true;
					break;
				case 'originpulse': case 'surf':
					if (hasMove['hydropump'] || hasMove['scald']) rejected = true;
					break;
				case 'scald':
					if (['liquidation', 'waterfall', 'waterpulse'].some(m => hasMove[m])) rejected = true;
					break;

				// Status:
				case 'electroweb': case 'stunspore': case 'thunderwave':
					if (counter.setupType || !!counter['speedsetup'] || (hasMove['rest'] && hasMove['sleeptalk'])) rejected = true;
					if (['discharge', 'spore', 'toxic', 'trickroom', 'yawn'].some(m => hasMove[m])) rejected = true;
					break;
				case 'glare': case 'headbutt':
					if (hasMove['bodyslam'] || !hasMove['glare']) rejected = true;
					break;
				case 'toxic':
					if (['hypnosis', 'sleeppowder', 'toxicspikes', 'willowisp', 'yawn'].some(m => hasMove[m])) rejected = true;
					if (counter.setupType || hasMove['flamecharge'] || hasMove['raindance']) rejected = true;
					break;
				case 'willowisp':
					if (hasMove['scald']) rejected = true;
					break;
				case 'raindance':
					if (counter.Physical + counter.Special < 2 || hasMove['rest'] && hasMove['sleeptalk']) rejected = true;
					if (!hasType['Water'] && !counter['Water']) rejected = true;
					break;
				case 'sunnyday':
					if (counter.Physical + counter.Special < 2 || hasMove['rest'] && hasMove['sleeptalk']) rejected = true;
					if (!hasAbility['Chlorophyll'] && !hasAbility['Flower Gift'] && !hasMove['solarbeam']) rejected = true;
					if (rejected && movePool.length > 1) {
						const solarbeam = movePool.indexOf('solarbeam');
						if (solarbeam >= 0) this.fastPop(movePool, solarbeam);
						if (movePool.length > 1) {
							const weatherball = movePool.indexOf('weatherball');
							if (weatherball >= 0) this.fastPop(movePool, weatherball);
						}
					}
					break;
				case 'painsplit': case 'recover': case 'roost': case 'synthesis':
					if (hasMove['leechseed'] || hasMove['rest']) rejected = true;
					break;
				case 'substitute':
					if (hasMove['dracometeor'] || hasMove['leafstorm'] && !hasAbility['Contrary']) rejected = true;
					if (['encore', 'pursuit', 'rest', 'taunt', 'uturn', 'voltswitch', 'whirlwind'].some(m => hasMove[m])) rejected = true;
					if (movePool.includes('copycat')) rejected = true;
					break;
				case 'powersplit':
					if (hasMove['guardsplit']) rejected = true;
					break;
				case 'wideguard':
					if (hasMove['protect']) rejected = true;
					break;
				}

				// This move doesn't satisfy our setup requirements:
				if (
					(move.category === 'Physical' && counter.setupType === 'Special') ||
					(move.category === 'Special' && counter.setupType === 'Physical')
				) {
					// Reject STABs last in case the setup type changes later on
					const stabs = counter[species.types[0]] + (counter[species.types[1]] || 0);
					if (
						!SetupException.includes(moveid) &&
						(!hasType[move.type] || stabs > 1 || counter[move.category] < 2)
					) rejected = true;
				}
				// Hidden Power isn't good enough
				if (
					counter.setupType === 'Special' &&
					moveid === 'hiddenpower' &&
					species.types.length > 1 &&
					counter['Special'] <= 2 &&
					!hasType[move.type] &&
					!counter['Physical'] &&
					counter['specialpool']
				) {
					rejected = true;
				}

				// Pokemon should have moves that benefit their Type/Ability/Weather, as well as moves required by its forme
				if (!rejected && !move.damage && !isSetup && !move.weather && !move.stallingMove &&
					(isDoubles || (
						!['judgment', 'lightscreen', 'reflect', 'sleeptalk', 'toxic'].includes(moveid) &&
						(move.category !== 'Status' || !move.flags.heal)
					)) && (
					!counter.setupType || counter.setupType === 'Mixed' ||
					(move.category !== counter.setupType && move.category !== 'Status') ||
					(counter[counter.setupType] + counter.Status > 3 && !counter.hazards)
				) && (
					(!counter.stab && !hasMove['nightshade'] && !hasMove['seismictoss'] && (
						species.types.length > 1 ||
						(species.types[0] !== 'Normal' && species.types[0] !== 'Psychic') ||
						!hasMove['icebeam'] ||
						species.baseStats.spa >= species.baseStats.spd)
					) || (hasType['Bug'] && (movePool.includes('megahorn') || movePool.includes('pinmissile'))) || (
						hasType['Dark'] &&
						!counter['Dark'] &&
						!hasAbility['Protean']
					) || (
						hasMove['suckerpunch'] && !hasAbility['Contrary'] && counter.stab < species.types.length
					) || (
						hasType['Dragon'] &&
						!counter['Dragon'] &&
						!hasAbility['Aerilate'] && !hasAbility['Pixilate'] &&
						!hasMove['fly'] && !hasMove['rest'] && !hasMove['sleeptalk']
					) || (hasType['Electric'] && (!counter['Electric'] || movePool.includes('thunder'))) ||
					(hasType['Fairy'] && !counter['Fairy'] && !hasType['Flying'] && !hasAbility['Pixilate']) ||
					(hasType['Fighting'] && (!counter['Fighting'] || !counter.stab)) ||
					(hasType['Fire'] && (!counter['Fire'] || movePool.includes('flareblitz') || movePool.includes('quiverdance'))) || (
						hasType['Flying'] &&
						!counter['Flying'] &&
						(hasAbility['Gale Wings'] || hasAbility['Serene Grace'] || (
							hasType['Normal'] && (movePool.includes('beakblast') || movePool.includes('bravebird'))
						))
					) || (
						hasType['Ghost'] &&
						(!counter['Ghost'] || movePool.includes('spectralthief')) &&
						!hasType['Dark'] &&
						!hasAbility['Steelworker']
					) || (hasType['Grass'] && !counter['Grass'] && (species.baseStats.atk >= 100 || movePool.includes('leafstorm'))) ||
					(hasType['Ground'] && !counter['Ground'] && !hasMove['rest'] && !hasMove['sleeptalk']) || (
						hasType['Ice'] && !hasAbility['Refrigerate'] && (
							!counter['Ice'] ||
							movePool.includes('iciclecrash') ||
							(hasAbility['Snow Warning'] && movePool.includes('blizzard'))
						)
					) || (hasType['Normal'] && movePool.includes('facade')) || (
						hasType['Poison'] &&
						!counter['Poison'] &&
						(counter.setupType || hasAbility['Adaptability'] || hasAbility['Sheer Force'] || movePool.includes('gunkshot'))
					) || (hasType['Psychic'] && !counter['Psychic'] && (
						hasAbility['Psychic Surge'] ||
						movePool.includes('psychicfangs') ||
						(!hasType['Flying'] && !hasAbility['Pixilate'] && counter.stab < species.types.length)
					)) || (
						hasType['Rock'] &&
						!counter['Rock'] &&
						!hasType['Fairy'] &&
						(counter.setupType === 'Physical' || species.baseStats.atk >= 105 || hasAbility['Rock Head'])
					) || (hasType['Steel'] && !counter['Steel'] && (species.baseStats.atk >= 100 || hasAbility['Steelworker'])) || (
						hasType['Water'] &&
						((!counter['Water'] && !hasAbility['Protean']) || !counter.stab || movePool.includes('crabhammer'))
					) || (
						hasAbility['Adaptability'] &&
						!counter.setupType &&
						species.types.length > 1 &&
						(!counter[species.types[0]] || !counter[species.types[1]])
					) || (
						!counter['Normal'] &&
						(hasAbility['Aerilate'] || hasAbility['Pixilate'] || (hasAbility['Refrigerate'] && !hasMove['blizzard']))
					) || (hasAbility['Contrary'] && !counter['contrary'] && species.name !== 'Shuckle') ||
					(hasAbility['Slow Start'] && movePool.includes('substitute')) ||
					(
						(['recover', 'roost', 'slackoff', 'softboiled'].some(m => movePool.includes(m))) &&
						counter.Status &&
						!counter.setupType &&
						['healingwish', 'trick', 'trickroom'].every(m => !hasMove[m])
					) || (
						movePool.includes('milkdrink') ||
						movePool.includes('shoreup') ||
						(movePool.includes('stickyweb') && !counter.setupType && !teamDetails.stickyWeb)
					) || (
						isLead &&
						movePool.includes('stealthrock') &&
						counter.Status && !counter.setupType &&
						!counter['speedsetup'] && !hasMove['substitute']
					) || (species.requiredMove && movePool.includes(toID(species.requiredMove)))
				)) {
					// Reject Status or non-STAB, or low basepower moves
					if (move.category === 'Status' || !hasType[move.type] || move.basePower && move.basePower < 40 && !move.multihit) {
						rejected = true;
					}
				}

				// Sleep Talk shouldn't be selected without Rest
				if (moveid === 'rest' && rejected) {
					const sleeptalk = movePool.indexOf('sleeptalk');
					if (sleeptalk >= 0) {
						if (movePool.length < 2) {
							rejected = false;
						} else {
							this.fastPop(movePool, sleeptalk);
						}
					}
				}

				// Remove rejected moves from the move list
				if (rejected && (
					movePool.length - availableHP ||
					(availableHP && (moveid === 'hiddenpower' || !hasMove['hiddenpower']))
				)) {
					if (move.category !== 'Status' && !move.damage && !move.flags.charge && (moveid !== 'hiddenpower' || !availableHP)) {
						rejectedPool.push(moves[k]);
					}
					moves.splice(k, 1);
					break;
				}
				if (rejected && rejectedPool.length) {
					moves.splice(k, 1);
					break;
				}
			}
		} while (moves.length < 4 && (movePool.length || rejectedPool.length));

		// Moveset modifications
		if (hasMove['autotomize'] && hasMove['heavyslam']) {
			if (species.id === 'celesteela') {
				moves[moves.indexOf('heavyslam')] = 'flashcannon';
			} else {
				moves[moves.indexOf('autotomize')] = 'rockpolish';
			}
		}
		if (hasMove['raindance'] && hasMove['thunderbolt'] && !isDoubles) {
			moves[moves.indexOf('thunderbolt')] = 'thunder';
		}
		if (hasMove['workup'] && !counter['Special'] && species.id === 'zeraora') {
			moves[moves.indexOf('workup')] = 'bulkup';
		}

		const battleOnly = species.battleOnly && !species.requiredAbility;
		const baseSpecies: Species = battleOnly ? this.dex.getSpecies(species.battleOnly as string) : species;
		const abilities: string[] = Object.values(baseSpecies.abilities);
		const defensiveStatTotal = species.baseStats.hp + species.baseStats.def + species.baseStats.spd;
		abilities.sort((a, b) => this.dex.getAbility(b).rating - this.dex.getAbility(a).rating);
		let ability0 = this.dex.getAbility(abilities[0]);
		let ability1 = this.dex.getAbility(abilities[1]);
		let ability2 = this.dex.getAbility(abilities[2]);
		if (abilities[1]) {
			if (abilities[2] && ability1.rating <= ability2.rating && this.randomChance(1, 2)) {
				[ability1, ability2] = [ability2, ability1];
			}
			if (ability0.rating <= ability1.rating && this.randomChance(1, 2)) {
				[ability0, ability1] = [ability1, ability0];
			} else if (ability0.rating - 0.6 <= ability1.rating && this.randomChance(2, 3)) {
				[ability0, ability1] = [ability1, ability0];
			}
			ability = ability0.name;

			let rejectAbility: boolean;
			do {
				rejectAbility = false;
				if ([
					'Battle Bond', 'Dazzling', 'Flare Boost', 'Hyper Cutter', 'Ice Body', 'Innards Out', 'Moody', 'Steadfast',
				].includes(ability)) {
					rejectAbility = true;
				} else if (['Aerilate', 'Galvanize', 'Pixilate', 'Refrigerate'].includes(ability)) {
					rejectAbility = !counter['Normal'];
				} else if (ability === 'Analytic' || ability === 'Download') {
					rejectAbility = species.nfe;
				} else if (ability === 'Battle Armor' || ability === 'Sturdy') {
					rejectAbility = (!!counter['recoil'] && !counter['recovery']);
				} else if (ability === 'Chlorophyll' || ability === 'Leaf Guard') {
					rejectAbility = (
						species.baseStats.spe > 100 ||
						abilities.includes('Harvest') ||
						(!hasMove['sunnyday'] && !teamDetails['sun'])
					);
				} else if (ability === 'Competitive') {
					rejectAbility = (!counter['Special'] || hasMove['rest'] && hasMove['sleeptalk']);
				} else if (ability === 'Compound Eyes' || ability === 'No Guard') {
					rejectAbility = !counter['inaccurate'];
				} else if (['Contrary', 'Iron Fist', 'Skill Link', 'Strong Jaw'].includes(ability)) {
					rejectAbility = !counter[toID(ability)];
				} else if (['Defiant', 'Justified', 'Moxie'].includes(ability)) {
					rejectAbility = (!counter['Physical'] || hasMove['dragontail']);
				} else if (ability === 'Flash Fire') {
					rejectAbility = abilities.includes('Drought');
				} else if (ability === 'Gluttony') {
					rejectAbility = !hasMove['bellydrum'];
				} else if (ability === 'Harvest') {
					rejectAbility = abilities.includes('Frisk');
				} else if (ability === 'Hustle') {
					rejectAbility = counter.Physical < 2;
				} else if (['Hydration', 'Rain Dish', 'Swift Swim'].includes(ability)) {
					rejectAbility = (species.baseStats.spe > 100 || !hasMove['raindance'] && !teamDetails['rain']);
				} else if (ability === 'Slush Rush' || ability === 'Snow Cloak') {
					rejectAbility = !teamDetails['hail'];
				} else if (ability === 'Immunity' || ability === 'Snow Warning') {
					rejectAbility = (hasMove['facade'] || hasMove['hypervoice']);
				} else if (ability === 'Intimidate') {
					rejectAbility = (hasMove['bodyslam'] || hasMove['rest'] || abilities.includes('Reckless') && counter['recoil'] > 1);
				} else if (ability === 'Lightning Rod') {
					rejectAbility = species.types.includes('Ground');
				} else if (ability === 'Limber') {
					rejectAbility = species.types.includes('Electric');
				} else if (ability === 'Liquid Voice') {
					rejectAbility = !counter['sound'];
				} else if (ability === 'Magic Guard' || ability === 'Speed Boost') {
					rejectAbility = (abilities.includes('Tinted Lens') && (!counter['Status'] || hasMove['uturn']));
				} else if (ability === 'Magician') {
					rejectAbility = hasMove['switcheroo'];
				} else if (ability === 'Magnet Pull') {
					rejectAbility = (!!counter['Normal'] || !hasType['Electric'] && !hasMove['earthpower']);
				} else if (ability === 'Mold Breaker') {
					rejectAbility = (
						hasMove['acrobatics'] || hasMove['sleeptalk'] ||
						abilities.includes('Adaptability') || abilities.includes('Iron Fist') ||
						(abilities.includes('Sheer Force') && counter['sheerforce'])
					);
				} else if (ability === 'Overgrow') {
					rejectAbility = !counter['Grass'];
				} else if (ability === 'Poison Heal') {
					rejectAbility = (abilities.includes('Technician') && !!counter['technician']);
				} else if (ability === 'Power Construct') {
					rejectAbility = species.forme === '10%';
				} else if (ability === 'Prankster') {
					rejectAbility = !counter['Status'];
				} else if (ability === 'Pressure' || ability === 'Synchronize') {
					rejectAbility = (counter.Status < 2 || !!counter['recoil'] || !!species.isMega);
				} else if (ability === 'Regenerator') {
					rejectAbility = abilities.includes('Magic Guard');
				} else if (ability === 'Quick Feet') {
					rejectAbility = hasMove['bellydrum'];
				} else if (ability === 'Reckless' || ability === 'Rock Head') {
					rejectAbility = (!counter['recoil'] || !!species.isMega);
				} else if (['Sand Force', 'Sand Rush', 'Sand Veil'].includes(ability)) {
					rejectAbility = !teamDetails['sand'];
				} else if (ability === 'Scrappy') {
					rejectAbility = !species.types.includes('Normal');
				} else if (ability === 'Serene Grace') {
					rejectAbility = (!counter['serenegrace'] || species.name === 'Blissey');
				} else if (ability === 'Sheer Force') {
					rejectAbility = (!counter['sheerforce'] || hasMove['doubleedge'] || abilities.includes('Guts') || !!species.isMega);
				} else if (ability === 'Simple') {
					rejectAbility = (!counter.setupType && !hasMove['flamecharge']);
				} else if (ability === 'Solar Power') {
					rejectAbility = (!counter['Special'] || !teamDetails['sun'] || !!species.isMega);
				} else if (ability === 'Swarm') {
					rejectAbility = (!counter['Bug'] || !!species.isMega);
				} else if (ability === 'Sweet Veil') {
					rejectAbility = hasType['Grass'];
				} else if (ability === 'Technician') {
					rejectAbility = (!counter['technician'] || hasMove['tailslap'] || !!species.isMega);
				} else if (ability === 'Tinted Lens') {
					rejectAbility = (
						hasMove['protect'] || !!counter['damage'] ||
						(counter.Status > 2 && !counter.setupType) ||
						abilities.includes('Prankster') ||
						(abilities.includes('Magic Guard') && !!counter['Status'])
					);
				} else if (ability === 'Torrent') {
					rejectAbility = (!counter['Water'] || !!species.isMega);
				} else if (ability === 'Unaware') {
					rejectAbility = (counter.setupType || abilities.includes('Magic Guard'));
				} else if (ability === 'Unburden') {
					rejectAbility = (!!species.isMega || abilities.includes('Prankster') || !counter.setupType && !hasMove['acrobatics']);
				} else if (ability === 'Water Absorb') {
					rejectAbility = hasMove['raindance'] || ['Drizzle', 'Unaware', 'Volt Absorb'].some(abil => abilities.includes(abil));
				} else if (ability === 'Weak Armor') {
					rejectAbility = counter.setupType !== 'Physical';
				}

				if (rejectAbility) {
					if (ability === ability0.name && ability1.rating >= 1) {
						ability = ability1.name;
					} else if (ability === ability1.name && abilities[2] && ability2.rating >= 1) {
						ability = ability2.name;
					} else {
						// Default to the highest rated ability if all are rejected
						ability = abilities[0];
						rejectAbility = false;
					}
				}
			} while (rejectAbility);

			if (
				abilities.includes('Guts') &&
				ability !== 'Quick Feet' &&
				(hasMove['facade'] || (hasMove['protect'] && !isDoubles) || (hasMove['rest'] && hasMove['sleeptalk']))
			) {
				ability = 'Guts';
			} else if (abilities.includes('Moxie') && (counter.Physical > 3 || hasMove['bounce']) && !isDoubles) {
				ability = 'Moxie';
			} else if (isDoubles) {
				if (abilities.includes('Intimidate')) ability = 'Intimidate';
				if (abilities.includes('Guts') && ability !== 'Intimidate') ability = 'Guts';
				if (abilities.includes('Storm Drain')) ability = 'Storm Drain';
				if (abilities.includes('Harvest')) ability = 'Harvest';
				if (abilities.includes('Unburden') && ability !== 'Prankster' && !species.isMega) ability = 'Unburden';
			}
			if (species.name === 'Ambipom' && !counter['technician']) {
				// If it doesn't qualify for Technician, Skill Link is useless on it
				ability = 'Pickup';
			}
		} else {
			ability = ability0.name;
		}

		item = !isDoubles ? 'Leftovers' : 'Sitrus Berry';
		if (species.requiredItems) {
			if (species.baseSpecies === 'Arceus' && (hasMove['judgment'] || !counter[species.types[0]] || teamDetails.zMove)) {
				// Judgment doesn't change type with Z-Crystals
				item = species.requiredItems[0];
			} else {
				item = this.sample(species.requiredItems);
			}

		// First, the extra high-priority items
		} else if (species.name === 'Decidueye' && hasMove['spiritshackle'] && counter.setupType && !teamDetails.zMove) {
			item = 'Decidium Z';
		} else if (species.name === 'Dedenne') {
			item = hasMove['substitute'] ? 'Petaya Berry' : 'Sitrus Berry';
		} else if (species.name === 'Deoxys-Attack') {
			item = (isLead && hasMove['stealthrock']) ? 'Focus Sash' : 'Life Orb';
		} else if (species.name === 'Farfetch\u2019d') {
			item = 'Stick';
		} else if (species.name === 'Genesect' && hasMove['technoblast']) {
			item = 'Douse Drive';
			forme = 'Genesect-Douse';
		} else if (species.name === 'Kommo-o' && !teamDetails.zMove) {
			item = hasMove['clangingscales'] ? 'Kommonium Z' : 'Dragonium Z';
		} else if (species.baseSpecies === 'Lycanroc' && hasMove['stoneedge'] && counter.setupType && !teamDetails.zMove) {
			item = 'Lycanium Z';
		} else if (species.baseSpecies === 'Marowak') {
			item = 'Thick Club';
		} else if (species.name === 'Marshadow' && hasMove['spectralthief'] && counter.setupType && !teamDetails.zMove) {
			item = 'Marshadium Z';
		} else if (species.name === 'Mimikyu' && hasMove['playrough'] && counter.setupType && !teamDetails.zMove) {
			item = 'Mimikium Z';
		} else if ((species.name === 'Necrozma-Dusk-Mane' || species.name === 'Necrozma-Dawn-Wings') && !teamDetails.zMove) {
			if (hasMove['autotomize'] && hasMove['sunsteelstrike']) {
				item = 'Solganium Z';
			} else if (hasMove['trickroom'] && hasMove['moongeistbeam']) {
				item = 'Lunalium Z';
			} else {
				item = 'Ultranecrozium Z';
				if (!hasMove['photongeyser']) {
					for (const moveid of moves) {
						const move = this.dex.getMove(moveid);
						if (move.category === 'Status' || hasType[move.type]) continue;
						moves[moves.indexOf(moveid)] = 'photongeyser';
						break;
					}
				}
			}
		} else if (species.name === 'Pikachu') {
			if (!isDoubles) {
				const pikachuForme = this.sample(['', '-Original', '-Hoenn', '-Sinnoh', '-Unova', '-Kalos', '-Alola', '-Partner']);
				forme = `Pikachu${pikachuForme}`;
			}
			if (forme !== 'Pikachu') ability = 'Static';
			item = 'Light Ball';
		} else if (
			!isDoubles &&
			species.name === 'Porygon-Z' &&
			hasMove['nastyplot'] &&
			!hasMove['trick'] &&
			!['nastyplot', 'icebeam', 'triattack'].includes(moves[0]) &&
			!teamDetails.zMove
		) {
			moves[moves.indexOf('nastyplot')] = 'conversion';
			moves[moves.indexOf('triattack')] = 'recover';
			item = 'Normalium Z';
		} else if (species.name === 'Raichu-Alola' && hasMove['thunderbolt'] && counter.setupType && !teamDetails.zMove) {
			item = 'Aloraichium Z';
		} else if (species.name === 'Shedinja' || species.name === 'Smeargle') {
			item = 'Focus Sash';
		} else if (species.name === 'Unfezant' && counter['Physical'] >= 2) {
			item = 'Scope Lens';
		} else if (species.name === 'Unown') {
			item = 'Choice Specs';
		} else if (species.name === 'Wobbuffet') {
			item = 'Custap Berry';
		} else if (ability === 'Harvest' || ability === 'Emergency Exit' && !!counter['Status']) {
			item = 'Sitrus Berry';
		} else if (ability === 'Imposter') {
			item = 'Choice Scarf';
		} else if (ability === 'Poison Heal') {
			item = 'Toxic Orb';
		} else if (species.evos.length) {
			item = (ability === 'Technician' && counter.Physical >= 4) ? 'Choice Band' : 'Eviolite';
		} else if (hasMove['switcheroo'] || hasMove['trick']) {
			if (species.baseStats.spe >= 60 && species.baseStats.spe <= 108) {
				item = 'Choice Scarf';
			} else {
				item = (counter.Physical > counter.Special) ? 'Choice Band' : 'Choice Specs';
			}
		} else if (hasMove['bellydrum']) {
			if (ability === 'Gluttony') {
				item = this.sample(['Aguav', 'Figy', 'Iapapa', 'Mago', 'Wiki']) + ' Berry';
			} else if (species.baseStats.spe <= 50 && !teamDetails.zMove && this.randomChance(1, 2)) {
				item = 'Normalium Z';
			} else {
				item = 'Sitrus Berry';
			}
		} else if (hasMove['copycat'] && counter.Physical >= 3) {
			item = 'Choice Band';
		} else if (hasMove['geomancy'] || hasMove['skyattack']) {
			item = 'Power Herb';
		} else if (hasMove['shellsmash']) {
			item = (ability === 'Solid Rock' && !!counter['priority']) ? 'Weakness Policy' : 'White Herb';
		} else if ((ability === 'Guts' || hasMove['facade']) && !hasMove['sleeptalk']) {
			item = (hasType['Fire'] || ability === 'Quick Feet' || ability === 'Toxic Boost') ? 'Toxic Orb' : 'Flame Orb';
		} else if (
			(ability === 'Magic Guard' && counter.damagingMoves.length > 1) ||
			(ability === 'Sheer Force' && counter['sheerforce'])
		) {
			item = 'Life Orb';
		} else if (ability === 'Unburden') {
			item = hasMove['fakeout'] ? 'Normal Gem' : 'Sitrus Berry';
		} else if (hasMove['acrobatics']) {
			item = '';
		} else if (
			hasMove['bugbuzz'] &&
			counter.setupType &&
			species.baseStats.spa > 100 &&
			!teamDetails.zMove
		) {
			item = 'Buginium Z';
		} else if (!teamDetails.zMove && (
			(hasMove['darkpulse'] && ability === 'Fur Coat' && counter.setupType) ||
			(hasMove['suckerpunch'] && ability === 'Moxie' && counter['Dark'] < 2)
		)) {
			item = 'Darkinium Z';
		} else if (hasMove['outrage'] && counter.setupType && !hasMove['fly'] && !teamDetails.zMove) {
			item = 'Dragonium Z';
		} else if (hasMove['electricterrain'] || ability === 'Electric Surge' && hasMove['thunderbolt']) {
			item = 'Electrium Z';
		} else if (hasMove['fleurcannon'] && !!counter['speedsetup'] && !teamDetails.zMove) {
			item = 'Fairium Z';
		} else if (!teamDetails.zMove && (
			(hasMove['focusblast'] && hasType['Fighting'] && counter.setupType) ||
			(hasMove['reversal'] && hasMove['substitute'])
		)) {
			item = 'Fightinium Z';
		} else if (hasMove['magmastorm'] && !teamDetails.zMove) {
			item = 'Firium Z';
		} else if (!teamDetails.zMove && (
			hasMove['fly'] ||
			(hasMove['hurricane'] && species.baseStats.spa >= 125 && (!!counter.Status || hasMove['superpower'])) ||
			((hasMove['bounce'] || hasMove['bravebird']) && counter.setupType)
		)) {
			item = 'Flyinium Z';
		} else if (!teamDetails.zMove && hasMove['shadowball'] && counter.setupType && ability === 'Beast Boost') {
			item = 'Ghostium Z';
		} else if (
			!teamDetails.zMove &&
			hasMove['sleeppowder'] && hasType['Grass'] &&
			counter.setupType && species.baseStats.spe <= 70
		) {
			item = 'Grassium Z';
		} else if (hasMove['dig'] && !teamDetails.zMove) {
			item = 'Groundium Z';
		} else if (hasMove['happyhour'] || hasMove['holdhands'] || (hasMove['encore'] && ability === 'Contrary')) {
			item = 'Normalium Z';
		} else if (hasMove['photongeyser'] && counter.setupType && !teamDetails.zMove) {
			item = 'Psychium Z';
		} else if (hasMove['stoneedge'] && hasType['Rock'] && hasMove['swordsdance'] && !teamDetails.zMove) {
			item = 'Rockium Z';
		} else if (hasMove['hydropump'] && ability === 'Battle Bond' && hasMove['uturn'] && !teamDetails.zMove) {
			item = 'Waterium Z';
		} else if (hasMove['solarbeam'] && ability !== 'Drought' && !hasMove['sunnyday'] && !teamDetails['sun']) {
			item = !teamDetails.zMove ? 'Grassium Z' : 'Power Herb';
		} else if ((hasMove['hail'] || (hasMove['blizzard'] && ability !== 'Snow Warning')) && !teamDetails.zMove) {
			item = 'Icium Z';
		} else if (hasMove['raindance']) {
			if (species.baseSpecies === 'Castform' && !teamDetails.zMove) {
				item = 'Waterium Z';
			} else {
				item = (ability === 'Forecast') ? 'Damp Rock' : 'Life Orb';
			}
		} else if (hasMove['sunnyday']) {
			if ((species.baseSpecies === 'Castform' || species.baseSpecies === 'Cherrim') && !teamDetails.zMove) {
				item = 'Firium Z';
			} else {
				item = (ability === 'Forecast') ? 'Heat Rock' : 'Life Orb';
			}
		} else if (hasMove['auroraveil'] || hasMove['lightscreen'] && hasMove['reflect']) {
			item = 'Light Clay';
		} else if (
			hasMove['rest'] && !hasMove['sleeptalk'] &&
			ability !== 'Natural Cure' && ability !== 'Shed Skin' && ability !== 'Shadow Tag'
		) {
			item = 'Chesto Berry';

		// Medium priority
		} else if (
			(ability === 'Speed Boost' || ability === 'Stance Change' || species.name === 'Pheromosa') &&
			counter.Physical + counter.Special > 2 &&
			!hasMove['uturn']
		) {
			item = 'Life Orb';
		} else if (isDoubles && hasMove['uturn'] && counter.Physical === 4 && !hasMove['fakeout']) {
			item = (
				species.baseStats.spe >= 60 && species.baseStats.spe <= 108 &&
				!counter['priority'] && this.randomChance(1, 2)
			) ? 'Choice Scarf' : 'Choice Band';
		} else if (isDoubles && counter.Special === 4 && hasMove['waterspout'] || hasMove['eruption']) {
			item = 'Choice Scarf';
		} else if (
			!isDoubles &&
			counter.Physical >= 4 &&
			['bodyslam', 'dragontail', 'fakeout', 'flamecharge', 'rapidspin', 'suckerpunch'].every(m => !hasMove[m])
		) {
			item = (
				(species.baseStats.atk >= 100 || ability === 'Huge Power') &&
				species.baseStats.spe >= 60 && species.baseStats.spe <= 108 &&
				!counter['priority'] &&
				this.randomChance(2, 3)
			) ? 'Choice Scarf' : 'Choice Band';
		} else if (
			!isDoubles &&
			(counter.Special >= 4 || (counter.Special >= 3 && hasMove['uturn'])) &&
			!hasMove['acidspray'] && !hasMove['clearsmog']
		) {
			item = (
				species.baseStats.spa >= 100 &&
				species.baseStats.spe >= 60 && species.baseStats.spe <= 108 &&
				ability !== 'Tinted Lens' &&
				!counter.Physical && !counter['priority'] &&
				this.randomChance(2, 3)
			) ? 'Choice Scarf' : 'Choice Specs';
		} else if (
			!isDoubles &&
			counter.Physical >= 3 &&
			hasMove['defog'] &&
			!hasMove['foulplay'] &&
			species.baseStats.spe >= 60 && species.baseStats.spe <= 108 &&
			!counter['priority']
		) {
			item = 'Choice Scarf';
		} else if ((ability === 'Drizzle' || ability === 'Slow Start' || species.name.includes('Rotom-') ||
			['aromatherapy', 'bite', 'clearsmog', 'curse', 'protect', 'sleeptalk'].some(m => hasMove[m])) && !isDoubles
		) {
			item = 'Leftovers';
		} else if (['endeavor', 'flail', 'reversal'].some(m => hasMove[m]) && ability !== 'Sturdy') {
			item = (ability === 'Defeatist') ? 'Expert Belt' : 'Focus Sash';
		} else if (hasMove['outrage'] && counter.setupType) {
			item = 'Lum Berry';
		} else if (
			isDoubles &&
			counter.damagingMoves.length >= 3 &&
			species.baseStats.spe >= 70 &&
			ability !== 'Multiscale' && ability !== 'Sturdy' && [
				'acidspray', 'electroweb', 'fakeout', 'feint', 'flamecharge', 'icywind',
				'incinerate', 'naturesmadness', 'rapidspin', 'snarl', 'suckerpunch', 'uturn',
			].every(m => !hasMove[m])
		) {
			item = (defensiveStatTotal >= 275) ? 'Sitrus Berry' : 'Life Orb';
		} else if (hasMove['substitute']) {
			item = counter.damagingMoves.length > 2 && !!counter['drain'] ? 'Life Orb' : 'Leftovers';
		} else if (
			!isDoubles &&
			this.dex.getEffectiveness('Ground', species) >= 2 &&
			ability !== 'Levitate' &&
			!hasMove['magnetrise']
		) {
			item = 'Air Balloon';
		} else if ((ability === 'Iron Barbs' || ability === 'Rough Skin') && this.randomChance(1, 2)) {
			item = 'Rocky Helmet';
		} else if (
			counter.Physical + counter.Special >= 4 &&
			species.baseStats.spd >= 50 && defensiveStatTotal >= 235) {
			item = 'Assault Vest';
		} else if (species.name === 'Palkia' && (hasMove['dracometeor'] || hasMove['spacialrend']) && hasMove['hydropump']) {
			item = 'Lustrous Orb';
		} else if (counter.damagingMoves.length >= 4) {
			item = (counter['Dragon'] || counter['Dark'] || counter['Normal']) ? 'Life Orb' : 'Expert Belt';
		} else if (counter.damagingMoves.length >= 3 && !!counter['speedsetup'] && defensiveStatTotal >= 300) {
			item = 'Weakness Policy';
		} else if (
			!isDoubles && isLead &&
			!['Regenerator', 'Sturdy'].includes(ability) &&
			!counter['recoil'] && !counter['recovery'] &&
			defensiveStatTotal < 255
		) {
			item = 'Focus Sash';

		// This is the "REALLY can't think of a good item" cutoff
		} else if (hasMove['stickyweb'] && ability === 'Sturdy') {
			item = 'Mental Herb';
		} else if (ability === 'Serene Grace' && hasMove['airslash'] && species.baseStats.spe > 100) {
			item = 'Metronome';
		} else if (ability === 'Sturdy' && hasMove['explosion'] && !counter['speedsetup']) {
			item = 'Custap Berry';
		} else if (ability === 'Super Luck') {
			item = 'Scope Lens';
		} else if (
			!isDoubles && counter.damagingMoves.length >= 3 && ability !== 'Sturdy' &&
			['acidspray', 'dragontail', 'foulplay', 'rapidspin', 'superfang', 'uturn'].every(m => !hasMove[m]) && (
				counter['speedsetup'] ||
				hasMove['trickroom'] ||
				(species.baseStats.spe > 40 && defensiveStatTotal < 275)
			)
		) {
			item = 'Life Orb';
		}

		// For Trick / Switcheroo
		if (item === 'Leftovers' && hasType['Poison']) {
			item = 'Black Sludge';
		}

		let level: number;

		if (!isDoubles) {
			const levelScale: {[k: string]: number} = {
				uber: 76, ou: 80, uu: 82, ru: 84, nu: 86, pu: 88,
			};
			const customScale: {[k: string]: number} = {
				// Banned Ability
				Dugtrio: 82, Gothitelle: 82, Pelipper: 84, Politoed: 84, Torkoal: 84, Wobbuffet: 82,
				// Holistic judgement
				'Castform-Rainy': 100, 'Castform-Snowy': 100, 'Castform-Sunny': 100, Delibird: 100, Spinda: 100, Unown: 100,
			};
			const tier = toID(species.tier).replace('bl', '');
			level = levelScale[tier] || (species.nfe ? 90 : 80);
			if (customScale[species.name]) level = customScale[species.name];
		} else {
			// We choose level based on BST. Min level is 70, max level is 99. 600+ BST is 70, less than 300 is 99. Calculate with those values.
			// Every 10.34 BST adds a level from 70 up to 99. Results are floored. Uses the Mega's stats if holding a Mega Stone
			const baseStats = species.baseStats;

			let bst = species.bst;
			// If Wishiwashi, use the school-forme's much higher stats
			if (species.baseSpecies === 'Wishiwashi') bst = this.dex.getSpecies('wishiwashischool').bst;
			// Adjust levels of mons based on abilities (Pure Power, Sheer Force, etc.) and also Eviolite
			// For the stat boosted, treat the Pokemon's base stat as if it were multiplied by the boost. (Actual effective base stats are higher.)
			const speciesAbility = (baseSpecies === species ? ability : species.abilities[0]);
			if (speciesAbility === 'Huge Power' || speciesAbility === 'Pure Power') {
				bst += baseStats.atk;
			} else if (speciesAbility === 'Parental Bond') {
				bst += 0.25 * (counter.Physical > counter.Special ? baseStats.atk : baseStats.spa);
			} else if (speciesAbility === 'Protean') {
				bst += 0.3 * (counter.Physical > counter.Special ? baseStats.atk : baseStats.spa);
			} else if (speciesAbility === 'Fur Coat') {
				bst += baseStats.def;
			} else if (speciesAbility === 'Slow Start') {
				bst -= baseStats.atk / 2 + baseStats.spe / 2;
			} else if (speciesAbility === 'Truant') {
				bst *= 2 / 3;
			}
			if (item === 'Eviolite') {
				bst += 0.5 * (baseStats.def + baseStats.spd);
			} else if (item === 'Light Ball') {
				bst += baseStats.atk + baseStats.spa;
			}
			level = 70 + Math.floor(((600 - Utils.clampIntRange(bst, 300, 600)) / 10.34));
		}

		// Prepare optimal HP
		const srWeakness = this.dex.getEffectiveness('Rock', species);
		while (evs.hp > 1) {
			const hp = Math.floor(Math.floor(2 * species.baseStats.hp + ivs.hp + Math.floor(evs.hp / 4) + 100) * level / 100 + 10);
			if (hasMove['substitute'] && hasMove['reversal']) {
				// Reversal users should be able to use four Substitutes
				if (hp % 4 > 0) break;
			} else if (hasMove['substitute'] && (
				item === 'Petaya Berry' || item === 'Sitrus Berry' ||
				(ability === 'Power Construct' && item !== 'Leftovers')
			)) {
				// Three Substitutes should activate Petaya Berry for Dedenne
				// Two Substitutes should activate Sitrus Berry or Power Construct
				if (hp % 4 === 0) break;
			} else if (hasMove['bellydrum'] && (item === 'Sitrus Berry' || ability === 'Gluttony')) {
				// Belly Drum should activate Sitrus Berry
				if (hp % 2 === 0) break;
			} else {
				// Maximize number of Stealth Rock switch-ins
				if (srWeakness <= 0 || hp % (4 / srWeakness) > 0) break;
			}
			evs.hp -= 4;
		}

		// Minimize confusion damage
		if (!counter['Physical'] && !hasMove['copycat'] && !hasMove['transform']) {
			evs.atk = 0;
			ivs.atk = 0;
		}

		if (ability === 'Beast Boost' && counter.Special < 1) {
			evs.spa = 0;
			ivs.spa = 0;
		}

		if (['gyroball', 'metalburst', 'trickroom'].some(m => hasMove[m])) {
			evs.spe = 0;
			ivs.spe = 0;
		}

		return {
			name: species.baseSpecies,
			species: forme,
			gender: species.gender,
			moves: moves,
			ability: ability,
			evs: evs,
			ivs: ivs,
			item: item,
			level: level,
			shiny: this.randomChance(1, 1024),
		};
	}

	randomTeam() {
		const seed = this.prng.seed;
		const ruleTable = this.dex.getRuleTable(this.format);
		const pokemon = [];

		// For Monotype
		const isMonotype = ruleTable.has('sametypeclause');
		const typePool = Object.keys(this.dex.data.TypeChart);
		const type = this.sample(typePool);

		const baseFormes: {[k: string]: number} = {};
		let hasMega = false;

		const tierCount: {[k: string]: number} = {};
		const typeCount: {[k: string]: number} = {};
		const typeComboCount: {[k: string]: number} = {};
		const teamDetails: RandomTeamsTypes.TeamDetails = {};

		// We make at most two passes through the potential Pokemon pool when creating a team - if the first pass doesn't
		// result in a team of six Pokemon we perform a second iteration relaxing as many restrictions as possible.
		for (const restrict of [true, false]) {
			if (pokemon.length >= 6) break;
			const pokemonPool = this.getPokemonPool(type, pokemon, isMonotype);
			while (pokemonPool.length && pokemon.length < 6) {
				const species = this.dex.getSpecies(this.sampleNoReplace(pokemonPool));

				// Check if the forme has moves for random battle
				if (this.format.gameType === 'singles') {
					if (!species.randomBattleMoves) continue;
				} else {
					if (!species.randomDoubleBattleMoves) continue;
				}
				if (!species.exists) continue;

				// Limit to one of each species (Species Clause)
				if (baseFormes[species.baseSpecies]) continue;

				// Limit one Mega per team
				if (hasMega && species.isMega) continue;

				// Adjust rate for species with multiple sets
				switch (species.baseSpecies) {
				case 'Arceus': case 'Silvally':
					if (this.randomChance(8, 9) && !isMonotype) continue;
					break;
				case 'Oricorio':
					if (this.randomChance(3, 4)) continue;
					break;
				case 'Castform': case 'Floette':
					if (this.randomChance(2, 3)) continue;
					break;
				case 'Aegislash': case 'Basculin': case 'Cherrim': case 'Gourgeist': case 'Groudon': case 'Kyogre': case 'Meloetta':
					if (this.randomChance(1, 2)) continue;
					break;
				case 'Greninja':
					if (this.gen >= 7 && this.randomChance(1, 2)) continue;
					break;
				}
				if (species.otherFormes && !hasMega && (
					species.otherFormes.includes(species.name + '-Mega') ||
					species.otherFormes.includes(species.name + '-Mega-X')
				)) {
					continue;
				}

				const tier = species.tier;
				const types = species.types;
				const typeCombo = types.slice().sort().join();

				if (restrict && !species.isMega) {
					// Limit one Pokemon per tier, two for Monotype
					if ((tierCount[tier] >= (isMonotype ? 2 : 1)) && !this.randomChance(1, Math.pow(5, tierCount[tier]))) {
						continue;
					}

					if (!isMonotype) {
						// Limit two of any type
						let skip = false;
						for (const typeName of types) {
							if (typeCount[typeName] > 1) {
								skip = true;
								break;
							}
						}
						if (skip) continue;
					}

					// Limit one of any type combination, two in Monotype
					if (typeComboCount[typeCombo] >= (isMonotype ? 2 : 1)) continue;
				}

				const set = this.randomSet(species, teamDetails, pokemon.length === 5, this.format.gameType !== 'singles');

				const item = this.dex.getItem(set.item);

				// Limit one Z-Move per team
				if (item.zMove && teamDetails['zMove']) continue;

				// Zoroark copies the last Pokemon
				if (set.ability === 'Illusion') {
					if (pokemon.length < 1) continue;
					set.level = pokemon[pokemon.length - 1].level;
				}

				// Okay, the set passes, add it to our team
				pokemon.unshift(set);

				// Don't bother tracking details for the 6th Pokemon
				if (pokemon.length === 6) break;

				// Now that our Pokemon has passed all checks, we can increment our counters
				baseFormes[species.baseSpecies] = 1;

				// Increment tier counter
				if (tierCount[tier]) {
					tierCount[tier]++;
				} else {
					tierCount[tier] = 1;
				}

				// Increment type counters
				for (const typeName of types) {
					if (typeName in typeCount) {
						typeCount[typeName]++;
					} else {
						typeCount[typeName] = 1;
					}
				}
				if (typeCombo in typeComboCount) {
					typeComboCount[typeCombo]++;
				} else {
					typeComboCount[typeCombo] = 1;
				}

				// Track what the team has
				if (item.megaStone) hasMega = true;
				if (item.zMove) teamDetails['zMove'] = 1;
				if (set.ability === 'Snow Warning' || set.moves.includes('hail')) teamDetails['hail'] = 1;
				if (set.moves.includes('raindance') || set.ability === 'Drizzle' && !item.onPrimal) teamDetails['rain'] = 1;
				if (set.ability === 'Sand Stream') teamDetails['sand'] = 1;
				if (set.moves.includes('sunnyday') || set.ability === 'Drought' && !item.onPrimal) teamDetails['sun'] = 1;
				if (set.moves.includes('spikes')) teamDetails['spikes'] = (teamDetails['spikes'] || 0) + 1;
				if (set.moves.includes('stealthrock')) teamDetails['stealthRock'] = 1;
				if (set.moves.includes('stickyweb')) teamDetails['stickyWeb'] = 1;
				if (set.moves.includes('toxicspikes')) teamDetails['toxicSpikes'] = 1;
				if (set.moves.includes('defog')) teamDetails['defog'] = 1;
				if (set.moves.includes('rapidspin')) teamDetails['rapidSpin'] = 1;
			}
		}
		if (pokemon.length < 6) throw new Error(`Could not build a random team for ${this.format} (seed=${seed})`);

		return pokemon;
	}

	randomFactorySets: AnyObject = require('./factory-sets.json');

	randomFactorySet(
		species: Species, teamData: RandomTeamsTypes.FactoryTeamDetails, tier: string
	): RandomTeamsTypes.RandomFactorySet | null {
		const id = toID(species.name);
		// const flags = this.randomFactorySets[tier][id].flags;
		const setList = this.randomFactorySets[tier][id].sets;

		const itemsMax: {[k: string]: number} = {
			choicespecs: 1,
			choiceband: 1,
			choicescarf: 1,
		};
		const movesMax: {[k: string]: number} = {
			rapidspin: 1,
			batonpass: 1,
			stealthrock: 1,
			defog: 1,
			spikes: 1,
			toxicspikes: 1,
		};
		const requiredMoves: {[k: string]: string} = {
			stealthrock: 'hazardSet',
			rapidspin: 'hazardClear',
			defog: 'hazardClear',
		};
		const weatherAbilitiesRequire: {[k: string]: string} = {
			hydration: 'raindance', swiftswim: 'raindance',
			leafguard: 'sunnyday', solarpower: 'sunnyday', chlorophyll: 'sunnyday',
			sandforce: 'sandstorm', sandrush: 'sandstorm', sandveil: 'sandstorm',
			slushrush: 'hail', snowcloak: 'hail',
		};
		const weatherAbilities = ['drizzle', 'drought', 'snowwarning', 'sandstream'];

		// Build a pool of eligible sets, given the team partners
		// Also keep track of sets with moves the team requires
		let effectivePool: {set: AnyObject, moveVariants?: number[]}[] = [];
		const priorityPool = [];
		for (const curSet of setList) {
			const item = this.dex.getItem(curSet.item);
			if (teamData.megaCount && teamData.megaCount > 0 && item.megaStone) continue; // reject 2+ mega stones
			if (teamData.zCount && teamData.zCount > 0 && item.zMove) continue; // reject 2+ Z stones
			if (itemsMax[item.id] && teamData.has[item.id] >= itemsMax[item.id]) continue;

			const ability = this.dex.getAbility(curSet.ability);
			if (weatherAbilitiesRequire[ability.id] && teamData.weather !== weatherAbilitiesRequire[ability.id]) continue;
			if (teamData.weather && weatherAbilities.includes(ability.id)) continue; // reject 2+ weather setters

			let reject = false;
			let hasRequiredMove = false;
			const curSetVariants = [];
			for (const move of curSet.moves) {
				const variantIndex = this.random(move.length);
				const moveId = toID(move[variantIndex]);
				if (movesMax[moveId] && teamData.has[moveId] >= movesMax[moveId]) {
					reject = true;
					break;
				}
				if (requiredMoves[moveId] && !teamData.has[requiredMoves[moveId]]) {
					hasRequiredMove = true;
				}
				curSetVariants.push(variantIndex);
			}
			if (reject) continue;
			effectivePool.push({set: curSet, moveVariants: curSetVariants});
			if (hasRequiredMove) priorityPool.push({set: curSet, moveVariants: curSetVariants});
		}
		if (priorityPool.length) effectivePool = priorityPool;

		if (!effectivePool.length) {
			if (!teamData.forceResult) return null;
			for (const curSet of setList) {
				effectivePool.push({set: curSet});
			}
		}

		const setData = this.sample(effectivePool);
		const moves = [];
		for (const [i, moveSlot] of setData.set.moves.entries()) {
			moves.push(setData.moveVariants ? moveSlot[setData.moveVariants[i]] : this.sample(moveSlot));
		}

		const item = Array.isArray(setData.set.item) ? this.sample(setData.set.item) : setData.set.item;
		const ability = Array.isArray(setData.set.ability) ? this.sample(setData.set.ability) : setData.set.ability;
		const nature = Array.isArray(setData.set.nature) ? this.sample(setData.set.nature) : setData.set.nature;

		return {
			name: setData.set.name || species.baseSpecies,
			species: setData.set.species,
			gender: setData.set.gender || species.gender || (this.randomChance(1, 2) ? 'M' : 'F'),
			item: item || '',
			ability: ability || species.abilities['0'],
			shiny: typeof setData.set.shiny === 'undefined' ? this.randomChance(1, 1024) : setData.set.shiny,
			level: setData.set.level ? setData.set.level : tier === "LC" ? 5 : 100,
			happiness: typeof setData.set.happiness === 'undefined' ? 255 : setData.set.happiness,
			evs: {hp: 0, atk: 0, def: 0, spa: 0, spd: 0, spe: 0, ...setData.set.evs},
			ivs: {hp: 31, atk: 31, def: 31, spa: 31, spd: 31, spe: 31, ...setData.set.ivs},
			nature: nature || 'Serious',
			moves: moves,
		};
	}

	randomFactoryTeam(side: PlayerOptions, depth = 0): RandomTeamsTypes.RandomFactorySet[] {
		const forceResult = (depth >= 4);

		// The teams generated depend on the tier choice in such a way that
		// no exploitable information is leaked from rolling the tier in getTeam(p1).
		const availableTiers = ['Uber', 'OU', 'UU', 'RU', 'NU', 'PU', 'LC', 'Mono'];
		if (!this.factoryTier) this.factoryTier = this.sample(availableTiers);
		const chosenTier = this.factoryTier;

		const tierValues: {[k: string]: number} = {
			Uber: 5,
			OU: 4, UUBL: 4,
			UU: 3, RUBL: 3,
			RU: 2, NUBL: 2,
			NU: 1, PUBL: 1,
			PU: 0,
		};

		const pokemon = [];
		const pokemonPool = Object.keys(this.randomFactorySets[chosenTier]);

		const typePool = Object.keys(this.dex.data.TypeChart);
		const type = this.sample(typePool);

		const teamData: TeamData = {
			typeCount: {}, typeComboCount: {}, baseFormes: {}, megaCount: 0, zCount: 0,
			has: {}, forceResult: forceResult, weaknesses: {}, resistances: {},
		};
		const requiredMoveFamilies = ['hazardSet', 'hazardClear'];
		const requiredMoves: {[k: string]: string} = {
			stealthrock: 'hazardSet',
			rapidspin: 'hazardClear',
			defog: 'hazardClear',
		};
		const weatherAbilitiesSet: {[k: string]: string} = {
			drizzle: 'raindance',
			drought: 'sunnyday',
			snowwarning: 'hail',
			sandstream: 'sandstorm',
		};
		const resistanceAbilities: {[k: string]: string[]} = {
			dryskin: ['Water'], waterabsorb: ['Water'], stormdrain: ['Water'],
			flashfire: ['Fire'], heatproof: ['Fire'],
			lightningrod: ['Electric'], motordrive: ['Electric'], voltabsorb: ['Electric'],
			sapsipper: ['Grass'],
			thickfat: ['Ice', 'Fire'],
			levitate: ['Ground'],
		};

		while (pokemonPool.length && pokemon.length < 6) {
			const species = this.dex.getSpecies(this.sampleNoReplace(pokemonPool));
			if (!species.exists) continue;

			// Lessen the need of deleting sets of Pokemon after tier shifts
			if (
				chosenTier in tierValues && species.tier in tierValues &&
				tierValues[species.tier] > tierValues[chosenTier]
			) continue;

			const speciesFlags = this.randomFactorySets[chosenTier][species.id].flags;

			// Limit to one of each species (Species Clause)
			if (teamData.baseFormes[species.baseSpecies]) continue;

			// Limit the number of Megas to one
			if (!teamData.megaCount) teamData.megaCount = 0;
			if (teamData.megaCount >= 1 && speciesFlags.megaOnly) continue;

			const set = this.randomFactorySet(species, teamData, chosenTier);
			if (!set) continue;

			const itemData = this.dex.getItem(set.item);

			// Actually limit the number of Megas to one
			if (teamData.megaCount >= 1 && itemData.megaStone) continue;

			// Limit the number of Z moves to one
			if (teamData.zCount && teamData.zCount >= 1 && itemData.zMove) continue;

			let types = species.types;

			// Enforce Monotype
			if (chosenTier === 'Mono') {
				// Prevents Mega Evolutions from breaking the type limits
				if (itemData.megaStone) {
					const megaSpecies = this.dex.getSpecies(itemData.megaStone);
					if (types.length > megaSpecies.types.length) types = [species.types[0]];
					// Only check the second type because a Mega Evolution should always share the first type with its base forme.
					if (megaSpecies.types[1] && types[1] && megaSpecies.types[1] !== types[1]) {
						types = [megaSpecies.types[0]];
					}
				}
				if (!types.includes(type)) continue;
			} else {
				// If not Monotype, limit to two of each type
				let skip = false;
				for (const typeName of types) {
					if (teamData.typeCount[typeName] > 1 && this.randomChance(4, 5)) {
						skip = true;
						break;
					}
				}
				if (skip) continue;

				// Limit 1 of any type combination
				let typeCombo = types.slice().sort().join();
				if (set.ability + '' === 'Drought' || set.ability + '' === 'Drizzle') {
				// Drought and Drizzle don't count towards the type combo limit
					typeCombo = set.ability + '';
				}
				if (typeCombo in teamData.typeComboCount) continue;
			}

			// Okay, the set passes, add it to our team
			pokemon.push(set);
			const typeCombo = types.slice().sort().join();
			// Now that our Pokemon has passed all checks, we can update team data:
			for (const typeName of types) {
				if (typeName in teamData.typeCount) {
					teamData.typeCount[typeName]++;
				} else {
					teamData.typeCount[typeName] = 1;
				}
			}
			teamData.typeComboCount[typeCombo] = 1;

			teamData.baseFormes[species.baseSpecies] = 1;

			if (itemData.megaStone) teamData.megaCount++;
			if (itemData.zMove) {
				if (!teamData.zCount) teamData.zCount = 0;
				teamData.zCount++;
			}
			if (itemData.id in teamData.has) {
				teamData.has[itemData.id]++;
			} else {
				teamData.has[itemData.id] = 1;
			}

			const abilityData = this.dex.getAbility(set.ability);
			if (abilityData.id in weatherAbilitiesSet) {
				teamData.weather = weatherAbilitiesSet[abilityData.id];
			}

			for (const move of set.moves) {
				const moveId = toID(move);
				if (moveId in teamData.has) {
					teamData.has[moveId]++;
				} else {
					teamData.has[moveId] = 1;
				}
				if (moveId in requiredMoves) {
					teamData.has[requiredMoves[moveId]] = 1;
				}
			}

			for (const typeName in this.dex.data.TypeChart) {
				// Cover any major weakness (3+) with at least one resistance
				if (teamData.resistances[typeName] >= 1) continue;
				if (resistanceAbilities[abilityData.id]?.includes(typeName) || !this.dex.getImmunity(typeName, types)) {
					// Heuristic: assume that Pok??mon with these abilities don't have (too) negative typing.
					teamData.resistances[typeName] = (teamData.resistances[typeName] || 0) + 1;
					if (teamData.resistances[typeName] >= 1) teamData.weaknesses[typeName] = 0;
					continue;
				}
				const typeMod = this.dex.getEffectiveness(typeName, types);
				if (typeMod < 0) {
					teamData.resistances[typeName] = (teamData.resistances[typeName] || 0) + 1;
					if (teamData.resistances[typeName] >= 1) teamData.weaknesses[typeName] = 0;
				} else if (typeMod > 0) {
					teamData.weaknesses[typeName] = (teamData.weaknesses[typeName] || 0) + 1;
				}
			}
		}
		if (pokemon.length < 6) return this.randomFactoryTeam(side, ++depth);

		// Quality control
		if (!teamData.forceResult) {
			for (const requiredFamily of requiredMoveFamilies) {
				if (!teamData.has[requiredFamily]) return this.randomFactoryTeam(side, ++depth);
			}
			for (const typeName in teamData.weaknesses) {
				if (teamData.weaknesses[typeName] >= 3) return this.randomFactoryTeam(side, ++depth);
			}
		}

		return pokemon;
	}

	randomBSSFactorySets: AnyObject = require('./bss-factory-sets.json');

	randomBSSFactorySet(
		species: Species, teamData: RandomTeamsTypes.FactoryTeamDetails
	): RandomTeamsTypes.RandomFactorySet | null {
		const id = toID(species.name);
		// const flags = this.randomBSSFactorySets[tier][id].flags;
		const setList = this.randomBSSFactorySets[id].sets;

		const movesMax: {[k: string]: number} = {
			batonpass: 1,
			stealthrock: 1,
			spikes: 1,
			toxicspikes: 1,
			doubleedge: 1,
			trickroom: 1,
		};
		const requiredMoves: {[k: string]: number} = {};
		const weatherAbilitiesRequire: {[k: string]: string} = {
			swiftswim: 'raindance',
			sandrush: 'sandstorm', sandveil: 'sandstorm',
		};
		const weatherAbilities = ['drizzle', 'drought', 'snowwarning', 'sandstream'];

		// Build a pool of eligible sets, given the team partners
		// Also keep track of sets with moves the team requires
		let effectivePool: {set: AnyObject, moveVariants?: number[], itemVariants?: number, abilityVariants?: number}[] = [];
		const priorityPool = [];
		for (const curSet of setList) {
			const item = this.dex.getItem(curSet.item);
			if (teamData.megaCount && teamData.megaCount > 1 && item.megaStone) continue; // reject 3+ mega stones
			if (teamData.zCount && teamData.zCount > 1 && item.zMove) continue; // reject 3+ Z stones
			if (teamData.has[item.id]) continue; // Item clause

			const ability = this.dex.getAbility(curSet.ability);
			if (weatherAbilitiesRequire[ability.id] && teamData.weather !== weatherAbilitiesRequire[ability.id]) continue;
			if (teamData.weather && weatherAbilities.includes(ability.id)) continue; // reject 2+ weather setters

			if (curSet.species === 'Aron' && teamData.weather !== 'sandstorm') continue; // reject Aron without a Sand Stream user

			let reject = false;
			let hasRequiredMove = false;
			const curSetVariants = [];
			for (const move of curSet.moves) {
				const variantIndex = this.random(move.length);
				const moveId = toID(move[variantIndex]);
				if (movesMax[moveId] && teamData.has[moveId] >= movesMax[moveId]) {
					reject = true;
					break;
				}
				if (requiredMoves[moveId] && !teamData.has[requiredMoves[moveId]]) {
					hasRequiredMove = true;
				}
				curSetVariants.push(variantIndex);
			}
			if (reject) continue;
			effectivePool.push({set: curSet, moveVariants: curSetVariants});
			if (hasRequiredMove) priorityPool.push({set: curSet, moveVariants: curSetVariants});
		}
		if (priorityPool.length) effectivePool = priorityPool;

		if (!effectivePool.length) {
			if (!teamData.forceResult) return null;
			for (const curSet of setList) {
				effectivePool.push({set: curSet});
			}
		}

		const setData = this.sample(effectivePool);
		const moves = [];
		for (const [i, moveSlot] of setData.set.moves.entries()) {
			moves.push(setData.moveVariants ? moveSlot[setData.moveVariants[i]] : this.sample(moveSlot));
		}

		return {
			name: setData.set.nickname || setData.set.name || species.baseSpecies,
			species: setData.set.species,
			gender: setData.set.gender || species.gender || (this.randomChance(1, 2) ? 'M' : 'F'),
			item: setData.set.item || '',
			ability: setData.set.ability || species.abilities['0'],
			shiny: typeof setData.set.shiny === 'undefined' ? this.randomChance(1, 1024) : setData.set.shiny,
			level: setData.set.level || 50,
			happiness: typeof setData.set.happiness === 'undefined' ? 255 : setData.set.happiness,
			evs: {hp: 0, atk: 0, def: 0, spa: 0, spd: 0, spe: 0, ...setData.set.evs},
			ivs: {hp: 31, atk: 31, def: 31, spa: 31, spd: 31, spe: 31, ...setData.set.ivs},
			nature: setData.set.nature || 'Serious',
			moves: moves,
		};
	}

	randomBSSFactoryTeam(side: PlayerOptions, depth = 0): RandomTeamsTypes.RandomFactorySet[] {
		const forceResult = (depth >= 4);

		const pokemon = [];

		const pokemonPool = Object.keys(this.randomBSSFactorySets);

		const teamData: TeamData = {
			typeCount: {}, typeComboCount: {}, baseFormes: {}, megaCount: 0, zCount: 0,
			eeveeLimCount: 0, has: {}, forceResult: forceResult, weaknesses: {}, resistances: {},
		};
		const requiredMoveFamilies: string[] = [];
		const requiredMoves: {[k: string]: string} = {};
		const weatherAbilitiesSet: {[k: string]: string} = {
			drizzle: 'raindance',
			drought: 'sunnyday',
			snowwarning: 'hail',
			sandstream: 'sandstorm',
		};
		const resistanceAbilities: {[k: string]: string[]} = {
			waterabsorb: ['Water'],
			flashfire: ['Fire'],
			lightningrod: ['Electric'], voltabsorb: ['Electric'],
			thickfat: ['Ice', 'Fire'],
			levitate: ['Ground'],
		};

		while (pokemonPool.length && pokemon.length < 6) {
			const species = this.dex.getSpecies(this.sampleNoReplace(pokemonPool));
			if (!species.exists) continue;

			const speciesFlags = this.randomBSSFactorySets[species.id].flags;
			if (!teamData.megaCount) teamData.megaCount = 0;

			// Limit to one of each species (Species Clause)
			if (teamData.baseFormes[species.baseSpecies]) continue;

			// Limit the number of Megas + Z-moves to 3
			if (teamData.megaCount + (teamData.zCount ? teamData.zCount : 0) >= 3 && speciesFlags.megaOnly) continue;

			// Limit 2 of any type
			const types = species.types;
			let skip = false;
			for (const type of types) {
				if (teamData.typeCount[type] > 1 && this.randomChance(4, 5)) {
					skip = true;
					break;
				}
			}
			if (skip) continue;

			// Restrict Eevee with certain Pokemon
			if (speciesFlags.limEevee) {
				if (!teamData.eeveeLimCount) teamData.eeveeLimCount = 0;
				teamData.eeveeLimCount++;
			}
			if (teamData.eeveeLimCount && teamData.eeveeLimCount >= 1 && speciesFlags.limEevee) continue;

			const set = this.randomBSSFactorySet(species, teamData);
			if (!set) continue;

			// Limit 1 of any type combination
			let typeCombo = types.slice().sort().join();
			if (set.ability === 'Drought' || set.ability === 'Drizzle') {
				// Drought and Drizzle don't count towards the type combo limit
				typeCombo = set.ability;
			}
			if (typeCombo in teamData.typeComboCount) continue;

			// Okay, the set passes, add it to our team
			pokemon.push(set);

			// Now that our Pokemon has passed all checks, we can update team data:
			for (const type of types) {
				if (type in teamData.typeCount) {
					teamData.typeCount[type]++;
				} else {
					teamData.typeCount[type] = 1;
				}
			}
			teamData.typeComboCount[typeCombo] = 1;

			teamData.baseFormes[species.baseSpecies] = 1;

			// Limit Mega and Z-move
			const itemData = this.dex.getItem(set.item);
			if (itemData.megaStone) teamData.megaCount++;
			if (itemData.zMove) {
				if (!teamData.zCount) teamData.zCount = 0;
				teamData.zCount++;
			}
			teamData.has[itemData.id] = 1;

			const abilityData = this.dex.getAbility(set.ability);
			if (abilityData.id in weatherAbilitiesSet) {
				teamData.weather = weatherAbilitiesSet[abilityData.id];
			}

			for (const move of set.moves) {
				const moveId = toID(move);
				if (moveId in teamData.has) {
					teamData.has[moveId]++;
				} else {
					teamData.has[moveId] = 1;
				}
				if (moveId in requiredMoves) {
					teamData.has[requiredMoves[moveId]] = 1;
				}
			}

			for (const typeName in this.dex.data.TypeChart) {
				// Cover any major weakness (3+) with at least one resistance
				if (teamData.resistances[typeName] >= 1) continue;
				if (resistanceAbilities[abilityData.id]?.includes(typeName) || !this.dex.getImmunity(typeName, types)) {
					// Heuristic: assume that Pok??mon with these abilities don't have (too) negative typing.
					teamData.resistances[typeName] = (teamData.resistances[typeName] || 0) + 1;
					if (teamData.resistances[typeName] >= 1) teamData.weaknesses[typeName] = 0;
					continue;
				}
				const typeMod = this.dex.getEffectiveness(typeName, types);
				if (typeMod < 0) {
					teamData.resistances[typeName] = (teamData.resistances[typeName] || 0) + 1;
					if (teamData.resistances[typeName] >= 1) teamData.weaknesses[typeName] = 0;
				} else if (typeMod > 0) {
					teamData.weaknesses[typeName] = (teamData.weaknesses[typeName] || 0) + 1;
				}
			}
		}
		if (pokemon.length < 6) return this.randomBSSFactoryTeam(side, ++depth);

		// Quality control
		if (!teamData.forceResult) {
			for (const requiredFamily of requiredMoveFamilies) {
				if (!teamData.has[requiredFamily]) return this.randomBSSFactoryTeam(side, ++depth);
			}
			for (const type in teamData.weaknesses) {
				if (teamData.weaknesses[type] >= 3) return this.randomBSSFactoryTeam(side, ++depth);
			}
		}

		return pokemon;
	}
}

export default RandomGen7Teams;
