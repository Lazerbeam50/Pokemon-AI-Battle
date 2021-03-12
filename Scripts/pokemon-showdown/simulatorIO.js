//Set up the battlestream
const Sim = require('pokemon-showdown');
stream = new Sim.BattleStream();

//Set up the IO library
const fsLibrary = require('fs');

//Define text variable
var outputText1 = "";
var outputText2 = ".";

(async () => {
    for await (const output of stream) {
        //console.log(output);
		outputText1 += "\n" + output
    }
})();

stream.write(`>start {"formatid":"gen4doublescustomgame"}`);

//Load teams
fsLibrary.readFile('team1-doc.txt', (error, teamText) => {
	if (error) throw error;
	var p1Team = teamText.toString();
	var p1Setup = `>player p1 {"name":"Alice","team":"` + p1Team + `"}`;
	console.log(p1Setup);
	stream.write(p1Setup);
});

fsLibrary.readFile('team2-doc.txt', (error, teamText) => {
	if (error) throw error;
	var p2Team = teamText.toString();
	var p2Setup = `>player p2 {"name":"Bob","team":"` + p2Team + `"}`;
	console.log(p2Setup);
	stream.write(p2Setup);
});


const readline = require('readline');
const r1 = readline.createInterface({
	input: process.stdin,
	output: process.stdout
});

function handle_IO(outputText2){
	//If the stream is done outputting, write text to output doc
	if (outputText1 == outputText2) {
		fsLibrary.writeFile('output-doc.txt', outputText1, (error) => {
			if (error) throw err;
		});
		outputText1 = "";
		outputText2 = ".";
	}
	else if (outputText1 == ""){
	}
	else{
		outputText2 = outputText1;
	}
	
	//Check if the input file has been updated
	fsLibrary.readFile('input-doc.txt', (error, inputText) => {
		if (error) throw error;
		if (inputText != ""){
			//If so, pass the text to the battlestream
			stream.write(inputText.toString().split("#")[0]);
			stream.write(inputText.toString().split("#")[1]);
			//Overwrite the input file with a blank string
			fsLibrary.writeFile('input-doc.txt', "", (error) => {
			if (error) throw err;
			});
		}
	});
	
	//Quit if the quit doc has been updated
	fsLibrary.readFile('quit-doc.txt', (error, quitText) => {
		if (error) throw error;
		if (quitText == "QUIT"){
			fsLibrary.writeFile('quit-doc.txt', "", (error) => {
				if (error) throw err;
				console.log("Quitting");
				throw error;
			})
		}
		else {
			setTimeout(function(){handle_IO(outputText2);}, 1000);
		}
	});
}

setTimeout(function(){handle_IO(outputText2);}, 1000);
	
