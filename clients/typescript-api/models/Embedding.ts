/**
 * OMF API
 * No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)
 *
 * OpenAPI spec version: 1.0.0
 * 
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import { HttpFile } from '../http/http';

/**
* Represents an embedding vector returned by embedding endpoint. 
*/
export class Embedding {
    /**
    * The index of the embedding in the list of embeddings.
    */
    'index': number;
    /**
    * The embedding vector, which is a list of floats. The length of vector depends on the model as listed in the [embedding guide](/docs/guides/embeddings). 
    */
    'embedding': Array<number>;
    /**
    * The object type, which is always \"embedding\"
    */
    'object': EmbeddingObjectEnum;

    static readonly discriminator: string | undefined = undefined;

    static readonly attributeTypeMap: Array<{name: string, baseName: string, type: string, format: string}> = [
        {
            "name": "index",
            "baseName": "index",
            "type": "number",
            "format": ""
        },
        {
            "name": "embedding",
            "baseName": "embedding",
            "type": "Array<number>",
            "format": ""
        },
        {
            "name": "object",
            "baseName": "object",
            "type": "EmbeddingObjectEnum",
            "format": ""
        }    ];

    static getAttributeTypeMap() {
        return Embedding.attributeTypeMap;
    }

    public constructor() {
    }
}


export enum EmbeddingObjectEnum {
    Embedding = 'embedding'
}

