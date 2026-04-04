import {
  EchoMessage,
  ResultsCounter,
  SearchPrompt,
  SelectedTrackPanel,
  SongsTable,
  StatusBar,
  TerminalHeader,
  TerminalOverlay,
} from './components/terminal';
import { WHATSAPP_LABEL, WHATSAPP_NUMBER } from './constants/terminal';
import { useRockTerminal } from './hooks/useRockTerminal';

function App() {
  const {
    query,
    setQuery,
    selectedIndex,
    selectedSong,
    totalSongs,
    filteredSongs,
    echoMessage,
    echoKey,
    selectSong,
    sendSelectedSongToWhatsApp,
  } = useRockTerminal({
    whatsAppNumber: WHATSAPP_NUMBER,
    whatsAppLabel: WHATSAPP_LABEL,
  });

  return (
    <div className="relative h-[100dvh] overflow-hidden bg-[radial-gradient(circle_at_10%_20%,#0a1907_0%,#030d02_45%,#020702_100%)] text-[#39ff14]">
      {/* <TerminalOverlay /> */}

      <main className="relative z-20 mx-auto flex h-full w-full max-w-[920px] flex-col overflow-hidden px-3 py-3 sm:px-5 sm:py-4">
        <TerminalHeader totalSongs={totalSongs} />
        <SearchPrompt query={query} onQueryChange={setQuery} />

        <div className="flex min-h-0 flex-1 flex-col">
          <ResultsCounter totalSongs={totalSongs} filteredCount={filteredSongs.length} />
          <SongsTable
            songs={filteredSongs}
            selectedIndex={selectedIndex}
            onSelectSong={selectSong}
          />
        </div>

        <SelectedTrackPanel
          selectedSong={selectedSong}
          whatsAppLabel={WHATSAPP_LABEL}
          onSend={sendSelectedSongToWhatsApp}
        />
        <EchoMessage message={echoMessage} echoKey={echoKey} />
        <StatusBar />
      </main>
    </div>
  );
}

export default App;
