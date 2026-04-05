import { useEffect } from 'react';
import {
  EchoMessage,
  ResultsCounter,
  SearchPrompt,
  SelectedTrackModal,
  SongsTable,
  StatusBar,
  TerminalHeader,
  TerminalOverlay,
} from './components/terminal';
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
    confirmSelection,
  } = useRockTerminal();

  useEffect(() => {
    const root = document.documentElement as HTMLElement & {
      webkitRequestFullscreen?: () => Promise<void> | void;
    };
    const documentWithWebkit = document as Document & { webkitFullscreenElement?: Element | null };

    const requestFullscreen = async () => {
      if (document.fullscreenElement || documentWithWebkit.webkitFullscreenElement) {
        return true;
      }

      try {
        if (root.requestFullscreen) {
          await root.requestFullscreen();
          return true;
        }
      } catch {
        // Ignore blocked requests in browsers with stricter fullscreen policies.
      }

      try {
        await root.webkitRequestFullscreen?.();
        return true;
      } catch {
        // Ignore unsupported webkit fullscreen API.
      }

      return false;
    };

    const removeListeners = () => {
      window.removeEventListener('pointerdown', onFirstInteraction, true);
      window.removeEventListener('touchstart', onFirstInteraction, true);
    };

    const onFirstInteraction = async () => {
      const enteredFullscreen = await requestFullscreen();
      if (enteredFullscreen || document.fullscreenElement || documentWithWebkit.webkitFullscreenElement) {
        removeListeners();
      }
    };

    window.addEventListener('pointerdown', onFirstInteraction, true);
    window.addEventListener('touchstart', onFirstInteraction, true);

    return () => {
      removeListeners();
    };
  }, []);

  return (
    <div className="relative h-[100dvh] overflow-hidden bg-[radial-gradient(circle_at_10%_20%,#0a1907_0%,#030d02_45%,#020702_100%)] text-[#39ff14]">
      <TerminalOverlay />

      <main className="relative z-20 mx-auto flex h-full w-full max-w-[920px] flex-col overflow-hidden px-2 py-2 sm:px-5 sm:py-4">
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

        <SelectedTrackModal
          selectedSong={selectedSong}
          onConfirm={confirmSelection}
          onClose={() => selectSong(null)}
        />
        <EchoMessage message={echoMessage} echoKey={echoKey} />
        <StatusBar />
      </main>
    </div>
  );
}

export default App;
