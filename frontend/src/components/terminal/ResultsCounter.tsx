type ResultsCounterProps = {
    totalSongs: number;
    filteredCount: number;
    isLoading: boolean;
    hasMoreResults: boolean;
};

function ResultsCounter({ totalSongs, filteredCount, isLoading, hasMoreResults }: ResultsCounterProps) {
    return (
        <div className="mb-1 text-[11px] text-[#1a7a00]">
            RESULTADOS: <span className="text-[#80ff60]">{filteredCount}</span> / {totalSongs}
            {isLoading ? <span className="ml-2 text-[#39ff14]">[sincronizando]</span> : null}
            {!isLoading && hasMoreResults ? <span className="ml-2"></span>: null}
        </div>
    );
}

export default ResultsCounter;
