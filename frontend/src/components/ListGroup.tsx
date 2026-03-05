import {useState} from "react";

interface Props {
    items: string[];
    heading?: string;
}

function ListGroup(
    {
        items,
        heading = "List"
    }: Props) {
    const [selectedIndex, setSelectedIndex] = useState(-1);
    const baseClass = 'w-full px-4 py-2 border-b border-gray-200 dark:border-gray-600 cursor-pointer';
    const selectedClass = 'bg-blue-500 text-white' + ' ' + baseClass;

    return <>
        <h1 className="text-3xl">{heading}</h1>
        <ul
            className="w-48 text-sm font-medium text-gray-900 bg-white border border-gray-200 rounded-lg
            dark:bg-gray-700 dark:border-gray-600 dark:text-white">
            {items.map((item, index) => <li
                    className={index === selectedIndex ? selectedClass : baseClass}
                    key={item}
                    onClick={() => setSelectedIndex(index)}
                >
                    {item}
                </li>
            )}
        </ul>
    </>
}

export default ListGroup;
