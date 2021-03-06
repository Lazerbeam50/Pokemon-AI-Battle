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

stream.write(`>start {"formatid":"gen4randombattle"}`);
stream.write(`>player p1 {"name":"Alice"}`);
stream.write(`>player p2 {"name":"Bob"}`);

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
	
