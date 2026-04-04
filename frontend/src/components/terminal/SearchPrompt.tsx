type SearchPromptProps = {
    query: string;
    onQueryChange: (value: string) => void;
};

function SearchPrompt({ query, onQueryChange }: SearchPromptProps) {
    return (
        <>
            <p className="mb-1 text-[12px] text-[#1a7a00]">$ grep -i "[SEARCH]" /db/rock_songs.db</p>

            <div className="mb-3 flex items-center gap-2 text-[14px] max-[760px]:flex-col max-[760px]:items-start">
                <span className="whitespace-nowrap font-terminal-display text-[21px] text-[#80ff60]">[root@rock ~]#</span>
                <div className="w-full flex-1">
                    <input
                        id="searchInput"
                        type="text"
                        value={query}
                        onChange={(event) => onQueryChange(event.target.value)}
                        placeholder="buscar cancion o artista..."
                        autoComplete="off"
                        spellCheck={false}
                        className="w-full border-0 border-b border-[#1a7a00] bg-transparent py-1 text-[14px] text-[#80ff60] outline-none placeholder:text-[#1a7a00] [caret-color:#80ff60] [text-shadow:0_0_8px_#39ff14]"
                    />
                </div>
            </div>
        </>
    );
}

export default SearchPrompt;
