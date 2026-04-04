type ResultsCounterProps = {
    totalSongs: number;
    filteredCount: number;
};

function ResultsCounter({ totalSongs, filteredCount }: ResultsCounterProps) {
    return (
        <div className="mb-[10px] border-b border-[#1a7a00] py-1 text-[11px] text-[#1a7a00]">
            RESULTADOS: <span className="text-[#80ff60]">{filteredCount}</span> / {totalSongs} canciones encontradas
        </div>
    );
}

export default ResultsCounter;
