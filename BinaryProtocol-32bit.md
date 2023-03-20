# Binary Protocol 32 bits (v0.1)

## Introduction

The Harp Binary Protocol is a binary communication protocol created in order to facilitate and unify the interaction between different devices. It was design with efficiency and parse ease in mind.

The protocol is based on addresses. Each address points to a certain position register available in the device. These positions are called registers.  Each register should have a defined data type and a meaning/purpose.

Although is not mandatory, usually the Harp Binary Protocol is exchanged between a Controller and a Peripheral. The Controller can be a computer, or a server and the Peripheral can be a data acquisition or an actuator device.

The available packets are:
 * Command: Sent by the Controller to the Peripheral. They allow to change the registers content and to read the registers content.
 * Reply: Sent by the Peripheral as an answer to a Command.
 * Event: Sent by the Peripheral when an external or internal event happens. An Event carry the content of a register.

Note that the Harp Binary Protocol uses Little-Endian for byte organization.

## Harp Message

The Harp Message consists of the necessary information to execute a well-informed exchange of data. It follows the next structure.

<style>
    table tr td {
        border-left: solid 1px;
        border-right: solid 1px;
        border-bottom: solid 1px;
    }
    table tr td.field {
        min-width: 2em;
        text-align: center;
    }
    table tr td.optional {
        background-color: gray;
    }
    table tr td.payload {
        background-color: blue;
        height: 3em;
    }
</style>

<table>
<tr>
    <td>31</td><td>...</td><td>24</td>
    <td>23</td><td>...</td><td>16</td>
    <td>15</td><td>...</td><td>8</td>
    <td>7</td><td>...</td><td>0</td>
</tr>
<tr>
    <td class="field" colspan="6">RegisterAddress</td>
    <td class="field" colspan="3">PayloadType</td>
    <td class="field" colspan="3">MessageType</td>
</tr>
<tr><td class="field" colspan="12">Length</td></tr>
<tr><td class="field optional" colspan="12">Port</td></tr>
<tr><td class="field optional" colspan="12">Seconds</td></tr>
<tr><td class="field optional" colspan="12">Nanoseconds</td></tr>
<tr><td class="field payload" colspan="12">Payload</td></tr>
<tr>
    <td class="field" colspan="6">Counter</td>
    <td class="field" colspan="6">Checksum</td>
</tr>
</table>

Gray background – Optional fields

Blue background – The field [Payload] can have more than one 32 bits word.

## MessageType

<table>
<tr>
    <td class="field">7</td>
    <td class="field">6</td>
    <td class="field">5</td>
    <td class="field">4</td>
    <td class="field">3</td>
    <td class="field">2</td>
    <td class="field">1</td>
    <td class="field">0</td>
</tr>
<tr>
    <td class="field">Flag32</td>
    <td class="field">0</td>
    <td class="field">0</td>
    <td class="field">FlagError</td>
    <td class="field">0</td>
    <td class="field">0</td>
    <td class="field" colspan="2">Type</td>
</tr>
</table>

### Type (2 bits)

|   Value   |  Description  |
| :-------  |  ----------- |
| 1 (Read)  |  Read the content of the register with address [RegisterAddress]  |
| 2 (Write) |   Write the content to the register with address [RegisterAddress]     |
| 3 (Event) |   Send the content of the register with address [RegisterAddress]     |

### FlagError (1 bit)

When this bit is set it means that an error occured. Examples of possible errors:

 *  Controller tries to read a register that doesn’t exist.
 * Controller tries to write unacceptable data to a certain register.
 * [PayloadType] doesn’t match with the register [RegisterAddress] type.

### Flag32 (1 bit)

When the Flag is asserted the current Harp Message is constructed according to the Harp Binary Protocol 32 bits. To comply with this document, this bit should always be equal to 1.

## PayloadType

<table>
<tr>
    <td class="field">7</td>
    <td class="field">6</td>
    <td class="field">5</td>
    <td class="field">4</td>
    <td class="field">3</td>
    <td class="field">2</td>
    <td class="field">1</td>
    <td class="field">0</td>
</tr>
<tr>
    <td class="field">IsSigned</td>
    <td class="field">IsFloat</td>
    <td class="field">0</td>
    <td class="field">HasTimestamp</td>
    <td class="field" colspan="4">Type</td>
</tr>
</table>

### Type (4 bits)

|  Value  |  Description  |
| :-----: |  -----------: |
| 1       |    8 bits     |
| 2       |   16 bits     |
| 4       |   32 bits     |
| 8       |   64 bits     |

### HasTimestamp (1 bit)

When this bit is asserted the Harp Message contains a timestamp. The fields [Seconds] and [NanoSeconds] are present in the message.

### IsFloat (1 bit)

This bit indicates if the [payload] contains rational values. If the bit is not asserted, the payload contains integers.

### IsSigned (1 bit)

If the bit is asserted, it indicates that the [payload] contains integers with signal.

> **Note:** The bits [IsFloat] and [IsSigned] must not be asserted at the same time.

## RegisterAddress

Contains the address to which register the Harp Message refers to.

## Length

Contains the number of 32-bit words that are still available and need to be read to complete the Harp Message.

## Port

This field is optional. If the device is a Hub of Harp Messages, it indicates the origin or destination of the Harp Message. If the field is not used or it’s equal to 0xFFFFFFFF, it points to the device itself.

## Seconds

It contains the seconds of the Harp Timestamp clock. This field is optional. In order to indicate that this field is available, the bit [HasTimestamp] in the field [PayloadType] needs to be asserted.

## Nanoseconds

It contains the fractional part of the Harp Timestamp clock in nanoseconds.

This field is optional. In order to indicate that this field is available, the bit [HasTimestamp] in the field [PayloadType] needs to be asserted.

## Payload

Contains the data to be transferred.

## Checksum

The checksum is equal to the U16 (unsigned 16 bits) sum of all the bytes of the Harp Message.

The receiver of the message should calculate the checksum and compare it with the received. If they don’t match, the Harp Message should be discarded.

## Counter

Contains a U16 (unsigned 16 bits) counter that starts from 0 (zero) when the device boots.

It should reset to 0 (zero) when the device goes to Active Mode.

