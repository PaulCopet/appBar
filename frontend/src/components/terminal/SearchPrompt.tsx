type SearchPromptProps = {
    query: string;
    onQueryChange: (value: string) => void;
};

function SearchPrompt({ query, onQueryChange }: SearchPromptProps) {
    return (
        <section className="mb-3 ">
            <p className="mb-2 text-[11px] tracking-[1px] text-[#1a7a00] sm:text-[12px]">
                [session@tty0] comando interactivo
            </p>

            <label htmlFor="searchInput" className="sr-only">
                Buscar cancion o artista en la terminal
            </label>

            <div className="flex flex-col text-[14px] leading-relaxed sm:text-[16px]">
                <div className="mb-1 font-terminal-display text-[20px] leading-none text-[#80ff60] [text-shadow:0_0_8px_#39ff14] sm:text-[22px]">
                    root@rock:/db/rock_songs.db#
                </div>

                <div className="flex w-full items-center">
                    <span className="mr-2 whitespace-nowrap text-[#39ff14]">$ grep -i</span>
                    <span className="text-[#1a7a00]">&quot;</span>

                    <div className="relative flex flex-1 items-center px-1">
                        <input
                            id="searchInput"
                            type="text"
                            value={query}
                            onChange={(event) => onQueryChange(event.target.value)}
                            placeholder="queen | ac/dc"
                            autoComplete="off"
                            spellCheck={false}
                            className="w-full border-b border-[#1a7a00]/70 bg-transparent px-2 py-1 text-[15px] text-[#80ff60] outline-none transition-all placeholder:text-[#1a7a00]/50 focus:border-[#39ff14] [caret-color:#39ff14] sm:text-[16px]"
                        />
                    </div>

                    <span className="text-[#1a7a00]">&quot;</span>
                </div>
            </div>
        </section>
    );
}

export default SearchPrompt;
