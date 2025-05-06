# DJAnalyzer - Progetto di analisi musicale

Progetto Djanalyzer:

questo progetto ha il fine di creare un programma software per poter lavorare su file audio canzoni che può agevolare il mio lavoro di dj.

 Per cui la prima cosa da creare è una interfaccia con dei pulsanti in orizzontale sotto i pulsanti ho messo uno spazio che deveessere lo spazio in cui viene scritto quello che il programma sta facendo ad ese se premo pulsante analisi,  lui deve scrivere la finestra sotto analisi J brani o del brano-
 poi sotto il titolo del branomusicale con quello che sta analizzando e quando ha finito con quello iniziare con l'altro scrivere il nome dell'altrocosì fino alla fine arrivato alla fine deve dire procedimento completato o analisi in questo caso completata.

 cosa essenziale da ricordare assolutamente.

 l'interfaccia che dovrebbe essere anche la cosa meno difficile potrebbe anche essere modificata però all'inizio va fatta con dei pulsanti in orizzontale almeno sei pulsanti sui quali verrà scritto il nome di quello che si vuole fare.
 e la cosa più importanteche il progetto deve essere modulare completamente modulare ogni sezione deve esse separata dalle altre  nel  senso che se viene modificato qualcosa in una sezione come può essere una variabile o un nome non va poi a intaccare altre parti di sezione causando problemi e continue correzioni di codice.

 questo non significa che ogni parte di codice verrà salvata separatamente….  tutto il programma sarà comunque riunito in un singolo programma.
 dovranno esserci all'inizio di ogni sezione delle note che descrivono cosa farà quella sezione in modo di arrivare subito a fare eventuali cambiamenti.

 struttura del programma:

 1 analisi 
 la prima cosa che deve fare il programma è avere un pulsante che dia la possibilità di aprire un file audio soprattutto MP3,  più file eventualmente premendo il controllo su ogni files  o addirittura tutta la cartella.
 il programma dovrà chiedere  immediatamente dopo questo il nome della cartella  perché comunque la cartella verrà salvata in automatico  nella cartella dove sono stati presi i files    con gli nome di  "risultati" 

 il programma deve analizzare i brani estraendo  i 
- BPM  la media dei battiti per minuto.
- la chiave melodica secondo la ruota di Camelot
 	una panoramica  la si trova a questo indirizzo:
	https://mixedinkey.com/harmonic-mixing-guide/?_gl=1*144azkn*_up*MQ..*_ga*NTY3NjkxNDUyLjE3NDY0ODgxNzM.*_ga_GQ7E42ETG5*czE3NDY0ODgxNzIkbzEkZzAkdDE3NDY0ODgxNzIkajAkbDAkaDA.

- subito dopo la chiave melodica   devono essere scritte le chiaviche  musicali compatibili  per un disagio armonico  che sono scritte sulla ruota di Camelot.

-l'energia  musicale della canzone varia da 1 a 10  anche se  quello che mi riguarda più dal cinque al 10 anzi verso 6 a 10 tutte lei Voler analizzare una cartella premendo s tutte le informazioni prese  da questo sito mixedinkey

https://mixedinkey.com/harmonic-mixing-guide/sorting-playlists-by-energy-level/

 eventualmente si può anche scrivere  il colore corrispondente sulla ruota di Camelot  in futuro magari  si potrebbero cambiare i colori in base all'energia  in modo da capire quali sono le canzoni che danno una certa energia o meno .

 per cui un esempio potrebbe essere 

nome del brano.mp3    BPM    Key     Key compatibili  EN (numero intero indicare energia  da uno a 10 )     colore

africa			96    C 	(C,F,G,Am)	6							colore corrispondente della ruota di Camelot


2-Quantizzazione
 premendo questo pulsante il programma dovrà chiedere  la cartella in cui è salvato il file  generato dal primo punto di analisi 
  controllare i  BPM  medi  controllare se La canzone ha  tempo costanteper cui corrispondente ai BPM oppure variabile  nel caso ci siano delle variazioni deve essere  effettuata una quantizzazione o stretch  sullo stile  di Ableton live,  praticamente fare in modo che  tutte le battute corrispondono senza avere variazioni  in modo da non  dove stare  rincorrere con la jogwheel come fece una volta con i giradischi  per tenera tempo le due tracce  quando due tracce sono perfettamente sincronizzate non c'è più bisogno di la ruota  del mixer  perché terranno il tempo esatto.
considerando che  i dj che sono abbastanza esperti sanno che  non si possono usare variazioni esagerate nel bissare due canzoni a meno che di fare  un sacchetto totale  cioè  finirono canzoni iniziare con l'altra anche se c'è il rischio di demolire il ritmo della gente che sta ballando .
 ma essendoci tante canzoni  da proporre  dovrebbe diventare una cosa rara perché  sono quantizzato bene  non c'è bisogno di stare a inseguirle  manualmente .
 una volta che il programma ha quantizzato una canzone  o nel caso non sia da quantizzare va comunque copiata  nella sotto cartella   quantizzazione tutte le canzoni 
 e nella cartella risultati  va salvato invece il file con  scritto  la percentuale  di quantizzazione effettuata.  non conosco bene la materia credo che ci siano anche dei pesi da dare  nel caso  i risultati non siano perfettamente  validi per cui si può  dare un peso maggiore per farlo diventare perfetto  in questo caso sarebbe meglio che  sia lo stesso programma  magari attraverso un algoritmo  AI  a scegliere lo stesso peso.  importante che alla fine  la qualità della canzone si è sempre uguale all'originale .


3- ottimizzazione
 il programma dovrà chiedere La lista che si vuole ordinare che potrebbe anche essere non quella quantizzata. 
l'ottimizzazione corrisponde Esclusivamente al riordino  delle canzoni  per  fare  dei mixaggi musicali  armonici  questo vuol dire chedovranno essere ordinate  secondo vari criteri  il primo criterio da considerare  è il BPM partendo dal BPM più basso a quello più alto,  la canzone successiva dovrà essere  possibilmente compatibile  con quella precedente  nella scala armonica  considerando un intervallo di quattro  battute  quindi non è detto che i BPM  possono essere costanti  ma possono essere ordinati anche  con intervalli di +/-  perché il secondo criterio è proprio quello di arrivare  a considerare ruota armonica di Camelot,  considerando sempre un intervallo  di quattro battute  che sta a significare che  dovrà essere fatto un'analisi  anche sulle canzoni successivi  per poter  proseguire  in un  mixaggio  armonico.  nel caso la differenza sia più di quattro battute  Il programma dovrà inserire la canzone più vicina alle quattro  che si agganci automaticamente al mixaggio armonico in modo da non dovere fare drastici cambiamenti  di mixaggio .
una volta  effettuato il riordino  il programma dovrà   chiedere se fare  il riordino  delle canzoni o fare un semplice  report.  nel caso di salvataggio delle canzoni il programma dovrà  team che mente copiare le canzoni dall'origine della prima lista che possono essere  quelle originale oppure  aver subito il processo di quantizzazione   e replicabile  esattamente nell'ordine  armonico descritto sopra  nella cartella.
Il  fatto di chiedere  prima se  salvare  l'ordine  anche delle canzoni cioè replicando le canzone però in ordine  di comanderanno eseguite nella playlist  dipende  se uno vuole correggere  anzi inserire  anche i  cue o no….

4- inserimento Cue o POI  secondolo schema di Virtualdj.
Usando il programma Virtualdj in modo prevalente,  premendo questo tasto il programma dovrà chiedere prima di tutto dove il file database.xml  di virtualdj,  in modo da poterlo leggere ed elaborare,  poi dovrà chiedere quale cartella elaborare una volta che conosce la cartella  deve solo  esaminare la canzone inserire fino a otto punti o  cue  che  sono delle specie di bandierine rovesciate  con un colore di cui sicuramente il più importante è il primo che deve essere  la prima battuta da cui deve partire  e qui  dove si posizionerà Virtualdj.  poi  analizzerà la canzone  inserendo  fino a otto  hot cue,  considerando soprattuttod ove  c'è   il cantato e  gli altri punti  del brano  dove ad esempio c'è solo  l'armonia  o percussioni che sono i punti più adatti per mix normali.  è anche  un'ottima idea  segnalare il punto più accattivante della canzone cioè il  drop….
 una volta analizzate queste dovrà inserire nel  file database.xml  i relativi  cue o hto cue in modo che caricata  la canzone avendo a  disposizione del suo data base  il valore  dei vari  cue  per ogni canzone, mettendo la canzone  nel relativo  spaz dove poi verrà avviata in riproduzione, la canzone  avrà già i suoi cue ben segnalati  e visibili.

 questo processo sicuramente sera poi ottimizzato anche in base ha altri  parametri magari più comodi o esplicativi per il dj.

5-  normalizzazione audio.
 praticamente sarebbe meglio utilizzare un algoritmo di intelligenza artificiale analizzare i volumi di ogni canzone e dopo aver chiesto i decibel cui si vuole portare il livello di tutto le canzoni il programma non dovrà fare altro che prendere le canzoni e adeguare il livello al valore stabilito normalmente è 89 dB manel caso uno voli ad esempio ascoltare poi le canzoni in autoradio o in riproduttore dove il volume basso può anche scegliere valore superiore ai 90.
 nel caso ci siano delle canzoni che vanno in saturazionea quel valorescelto il programma dovrà indicare in rosso nella lista la canzone non portandola a quel valore ma al valore più vicino perché non sia in saturazione.
 questa tecnica non  così completa  è  preso da un programma di pubblico dominio che si chiama mp3gain.
potrebbe essere  contemplato anche un algoritmo  per  agire  sui controlli di tono della canzone del caso  ci fossero pochi bassi o pochi alti.
 ma questo potrebbe essere poi integrato anche in una separazione  delle tracce audio  batteria bassi voce ecc  in modo da poter alzare proprio eccetera separatamente le cose ma è una cosa  futuristica.

-----

 espressioni future:
 creazione di una  grid  con quattro colori  Sfumati ben  separati da una linea  di diverso colore,  in cui  il colore più chiaro nella prima battuta e il colore più scuro o pieno  è la quarta battuta…  ripetuto ovviamente fino alla fine della canzone.
sopra questa griglia si posizionerà la canzone  con i picchi di batteria Di basso che dovrebbe essere quelli che indicano le battute  per visualizzare  graficamente  se la canzone è stata quantizzata in modo ottimale ho bisogno  di un'ottimizzazione più forte , deve essere dotato di uno zoom  in modo da confrontare  proprio preciso se il picco  finisce sulla linea che separa due  tonalità.  questo sarà agevolato dall'inserimento di un  metronomo  che  selezionato quando partirà la canzone sul player inizierà a  scandire  le battute con un suono  sulla prima  differente dalle altre tre .  
 integrazione con  spek  che mostra esattamente La qualità della canzone attraverso un grafico in cui è presente  i kilohertz a cui arriva la canzone  questo perché tante MP3 sono  marcati comma 320 e poi magari sono  tagliati a 10 kHz  per cui  non vanno bene  perché di scarsa qualità.
 separazione  degli stems.
player  per ascoltare la canzone.
pause per  Poter cambiare il ciclo di lavoro o aggiungere qualcosa.




 tutto questo lavoro sarà presente su  GITHUB  in modo che  al Chatgpt.  posso ogni volta capire esattamente di cosa sta facendo per cui con tutte le modifiche salvateportare avanti il lavoro da dove si è arrivati 

