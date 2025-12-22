/**
 * RptToXml - Crystal Reports to XML Extractor (Java Edition)
 *
 * Cross-platform tool to extract Crystal Reports (.rpt) structure to XML format.
 * Works on Windows, Linux, and macOS using the Crystal Reports Java SDK.
 *
 * Usage:
 *   java -jar RptToXml.jar <input.rpt> [output.xml]
 *   java -jar RptToXml.jar -r <directory>    (recursive)
 *
 * Copyright (c) 2024 RPT-to-RDF Project
 */
package com.rpttoxml;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

import com.crystaldecisions.sdk.occa.report.application.ReportClientDocument;
import com.crystaldecisions.sdk.occa.report.application.DataDefController;
import com.crystaldecisions.sdk.occa.report.application.DatabaseController;
import com.crystaldecisions.sdk.occa.report.application.ReportDefController;
import com.crystaldecisions.sdk.occa.report.application.SubreportController;
import com.crystaldecisions.sdk.occa.report.data.*;
import com.crystaldecisions.sdk.occa.report.definition.*;
import com.crystaldecisions.sdk.occa.report.lib.*;

/**
 * Main class for extracting Crystal Reports structure to XML.
 */
public class RptToXml {

    private static final String VERSION = "1.0.0";
    private boolean verbose = false;

    public static void main(String[] args) {
        RptToXml extractor = new RptToXml();

        if (args.length == 0) {
            printUsage();
            System.exit(1);
        }

        try {
            if (args[0].equals("-h") || args[0].equals("--help")) {
                printUsage();
                System.exit(0);
            }

            if (args[0].equals("-v") || args[0].equals("--version")) {
                System.out.println("RptToXml (Java Edition) version " + VERSION);
                System.exit(0);
            }

            if (args[0].equals("-r") || args[0].equals("--recursive")) {
                if (args.length < 2) {
                    System.err.println("Error: Directory path required for recursive mode");
                    System.exit(1);
                }
                extractor.processDirectory(args[1]);
            } else {
                String inputPath = args[0];
                String outputPath = args.length > 1 ? args[1] : null;
                extractor.processFile(inputPath, outputPath);
            }

        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            if (extractor.verbose) {
                e.printStackTrace();
            }
            System.exit(1);
        }
    }

    private static void printUsage() {
        System.out.println("RptToXml (Java Edition) - Crystal Reports to XML Extractor");
        System.out.println("Version " + VERSION);
        System.out.println();
        System.out.println("Usage:");
        System.out.println("  java -jar RptToXml.jar <input.rpt> [output.xml]");
        System.out.println("  java -jar RptToXml.jar -r <directory>");
        System.out.println();
        System.out.println("Options:");
        System.out.println("  -r, --recursive    Process all .rpt files in directory recursively");
        System.out.println("  -h, --help         Show this help message");
        System.out.println("  -v, --version      Show version information");
        System.out.println();
        System.out.println("Examples:");
        System.out.println("  java -jar RptToXml.jar report.rpt");
        System.out.println("  java -jar RptToXml.jar report.rpt output.xml");
        System.out.println("  java -jar RptToXml.jar -r ./reports/");
    }

    /**
     * Process all RPT files in a directory recursively.
     */
    public void processDirectory(String dirPath) throws Exception {
        Path dir = Paths.get(dirPath);
        if (!Files.isDirectory(dir)) {
            throw new IllegalArgumentException("Not a directory: " + dirPath);
        }

        List<Path> rptFiles = new ArrayList<>();
        Files.walk(dir)
            .filter(p -> p.toString().toLowerCase().endsWith(".rpt"))
            .forEach(rptFiles::add);

        System.out.println("Found " + rptFiles.size() + " RPT files");

        int success = 0;
        int failed = 0;

        for (Path rptFile : rptFiles) {
            try {
                String outputPath = rptFile.toString().replaceAll("(?i)\\.rpt$", ".xml");
                processFile(rptFile.toString(), outputPath);
                success++;
            } catch (Exception e) {
                System.err.println("Failed: " + rptFile + " - " + e.getMessage());
                failed++;
            }
        }

        System.out.println();
        System.out.println("Complete: " + success + " successful, " + failed + " failed");
    }

    /**
     * Process a single RPT file and extract to XML.
     */
    public void processFile(String inputPath, String outputPath) throws Exception {
        File inputFile = new File(inputPath);
        if (!inputFile.exists()) {
            throw new IllegalArgumentException("File not found: " + inputPath);
        }

        if (outputPath == null) {
            outputPath = inputPath.replaceAll("(?i)\\.rpt$", ".xml");
        }

        System.out.println("Processing: " + inputPath);

        ReportClientDocument clientDoc = new ReportClientDocument();

        try {
            // Open the report
            clientDoc.open(inputPath, 0);

            // Extract to XML
            Document xmlDoc = extractReportToXml(clientDoc, inputFile.getName());

            // Write XML to file
            writeXmlToFile(xmlDoc, outputPath);

            System.out.println("Output: " + outputPath);

        } finally {
            // Always close to release resources
            try {
                clientDoc.close();
            } catch (Exception e) {
                // Ignore close errors
            }
        }
    }

    /**
     * Extract report structure to XML document.
     */
    private Document extractReportToXml(ReportClientDocument clientDoc, String reportName) throws Exception {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        DocumentBuilder builder = factory.newDocumentBuilder();
        Document doc = builder.newDocument();

        // Root element
        Element root = doc.createElement("CrystalReport");
        root.setAttribute("name", reportName);
        root.setAttribute("extractedBy", "RptToXml-Java");
        root.setAttribute("version", VERSION);
        doc.appendChild(root);

        // Get controllers
        DataDefController dataDefController = clientDoc.getDataDefController();
        DatabaseController dbController = clientDoc.getDatabaseController();
        ReportDefController reportDefController = clientDoc.getReportDefController();
        SubreportController subreportController = clientDoc.getSubreportController();

        // Extract data definition
        extractDataDefinition(doc, root, dataDefController);

        // Extract database info
        extractDatabase(doc, root, dbController);

        // Extract report definition (layout)
        extractReportDefinition(doc, root, reportDefController, clientDoc);

        // Extract subreports
        extractSubreports(doc, root, subreportController);

        return doc;
    }

    /**
     * Extract data definition: formulas, parameters, groups, etc.
     */
    private void extractDataDefinition(Document doc, Element root, DataDefController dataDefController) {
        try {
            IDataDefinition dataDef = dataDefController.getDataDefinition();

            Element dataDefElement = doc.createElement("DataDefinition");
            root.appendChild(dataDefElement);

            // Formula fields
            extractFormulaFields(doc, dataDefElement, dataDef);

            // Parameter fields
            extractParameterFields(doc, dataDefElement, dataDef);

            // Groups
            extractGroups(doc, dataDefElement, dataDef);

            // Sort fields
            extractSortFields(doc, dataDefElement, dataDef);

            // Summary fields
            extractSummaryFields(doc, dataDefElement, dataDef);

            // Running total fields
            extractRunningTotalFields(doc, dataDefElement, dataDef);

        } catch (Exception e) {
            addErrorElement(doc, root, "DataDefinition", e);
        }
    }

    /**
     * Extract formula fields.
     */
    private void extractFormulaFields(Document doc, Element parent, IDataDefinition dataDef) {
        try {
            Element formulasElement = doc.createElement("FormulaFields");
            parent.appendChild(formulasElement);

            Fields formulaFields = dataDef.getFormulaFields();
            for (int i = 0; i < formulaFields.size(); i++) {
                IFormulaField formula = (IFormulaField) formulaFields.get(i);

                Element formulaElement = doc.createElement("FormulaField");
                formulaElement.setAttribute("name", safeString(formula.getName()));
                formulaElement.setAttribute("headingText", safeString(formula.getHeadingText()));

                // Formula text
                Element textElement = doc.createElement("Text");
                textElement.setTextContent(safeString(formula.getText()));
                formulaElement.appendChild(textElement);

                // Syntax
                FormulaSyntax syntax = formula.getSyntax();
                if (syntax != null) {
                    formulaElement.setAttribute("syntax", syntax.toString());
                }

                // Value type
                FieldValueType valueType = formula.getType();
                if (valueType != null) {
                    formulaElement.setAttribute("valueType", valueType.toString());
                }

                formulasElement.appendChild(formulaElement);
            }
        } catch (Exception e) {
            addErrorElement(doc, parent, "FormulaFields", e);
        }
    }

    /**
     * Extract parameter fields.
     */
    private void extractParameterFields(Document doc, Element parent, IDataDefinition dataDef) {
        try {
            Element paramsElement = doc.createElement("ParameterFields");
            parent.appendChild(paramsElement);

            Fields paramFields = dataDef.getParameterFields();
            for (int i = 0; i < paramFields.size(); i++) {
                IParameterField param = (IParameterField) paramFields.get(i);

                Element paramElement = doc.createElement("ParameterField");
                paramElement.setAttribute("name", safeString(param.getName()));
                paramElement.setAttribute("promptText", safeString(param.getPromptText()));
                paramElement.setAttribute("reportName", safeString(param.getReportName()));

                // Value type
                FieldValueType valueType = param.getType();
                if (valueType != null) {
                    paramElement.setAttribute("valueType", valueType.toString());
                }

                // Allow multiple values
                paramElement.setAttribute("allowMultipleValues",
                    String.valueOf(param.getAllowMultipleValue()));

                // Allow null
                paramElement.setAttribute("allowNullValue",
                    String.valueOf(param.getAllowNullValue()));

                // Default values
                try {
                    IParameterFieldDiscreteValue defaultValue = param.getCurrentValue();
                    if (defaultValue != null) {
                        Element defaultElement = doc.createElement("DefaultValue");
                        defaultElement.setTextContent(safeString(defaultValue.getValue()));
                        paramElement.appendChild(defaultElement);
                    }
                } catch (Exception e) {
                    // No default value
                }

                paramsElement.appendChild(paramElement);
            }
        } catch (Exception e) {
            addErrorElement(doc, parent, "ParameterFields", e);
        }
    }

    /**
     * Extract groups.
     */
    private void extractGroups(Document doc, Element parent, IDataDefinition dataDef) {
        try {
            Element groupsElement = doc.createElement("Groups");
            parent.appendChild(groupsElement);

            Groups groups = dataDef.getGroups();
            for (int i = 0; i < groups.size(); i++) {
                IGroup group = groups.get(i);

                Element groupElement = doc.createElement("Group");
                groupElement.setAttribute("conditionFieldName",
                    safeString(group.getConditionField().getName()));

                // Sort direction
                GroupSortOrder sortOrder = group.getSortOrder();
                if (sortOrder != null) {
                    groupElement.setAttribute("sortOrder", sortOrder.toString());
                }

                groupsElement.appendChild(groupElement);
            }
        } catch (Exception e) {
            addErrorElement(doc, parent, "Groups", e);
        }
    }

    /**
     * Extract sort fields.
     */
    private void extractSortFields(Document doc, Element parent, IDataDefinition dataDef) {
        try {
            Element sortsElement = doc.createElement("SortFields");
            parent.appendChild(sortsElement);

            SortFields sorts = dataDef.getSortFields();
            for (int i = 0; i < sorts.size(); i++) {
                ISortField sort = sorts.get(i);

                Element sortElement = doc.createElement("SortField");
                sortElement.setAttribute("fieldName", safeString(sort.getField().getName()));

                SortDirection direction = sort.getDirection();
                if (direction != null) {
                    sortElement.setAttribute("direction", direction.toString());
                }

                sortsElement.appendChild(sortElement);
            }
        } catch (Exception e) {
            addErrorElement(doc, parent, "SortFields", e);
        }
    }

    /**
     * Extract summary fields.
     */
    private void extractSummaryFields(Document doc, Element parent, IDataDefinition dataDef) {
        try {
            Element summariesElement = doc.createElement("SummaryFields");
            parent.appendChild(summariesElement);

            Fields summaryFields = dataDef.getSummaryFields();
            for (int i = 0; i < summaryFields.size(); i++) {
                ISummaryField summary = (ISummaryField) summaryFields.get(i);

                Element summaryElement = doc.createElement("SummaryField");
                summaryElement.setAttribute("name", safeString(summary.getName()));

                // Summary operation
                SummaryOperation operation = summary.getOperation();
                if (operation != null) {
                    summaryElement.setAttribute("operation", operation.toString());
                }

                // Summarized field
                IField summarizedField = summary.getSummarizedField();
                if (summarizedField != null) {
                    summaryElement.setAttribute("summarizedField",
                        safeString(summarizedField.getName()));
                }

                summariesElement.appendChild(summaryElement);
            }
        } catch (Exception e) {
            addErrorElement(doc, parent, "SummaryFields", e);
        }
    }

    /**
     * Extract running total fields.
     */
    private void extractRunningTotalFields(Document doc, Element parent, IDataDefinition dataDef) {
        try {
            Element runningTotalsElement = doc.createElement("RunningTotalFields");
            parent.appendChild(runningTotalsElement);

            Fields rtFields = dataDef.getRunningTotalFields();
            for (int i = 0; i < rtFields.size(); i++) {
                IRunningTotalField rt = (IRunningTotalField) rtFields.get(i);

                Element rtElement = doc.createElement("RunningTotalField");
                rtElement.setAttribute("name", safeString(rt.getName()));

                // Operation
                SummaryOperation operation = rt.getOperation();
                if (operation != null) {
                    rtElement.setAttribute("operation", operation.toString());
                }

                // Summarized field
                IField summarizedField = rt.getSummarizedField();
                if (summarizedField != null) {
                    rtElement.setAttribute("summarizedField",
                        safeString(summarizedField.getName()));
                }

                runningTotalsElement.appendChild(rtElement);
            }
        } catch (Exception e) {
            addErrorElement(doc, parent, "RunningTotalFields", e);
        }
    }

    /**
     * Extract database information.
     */
    private void extractDatabase(Document doc, Element root, DatabaseController dbController) {
        try {
            Element dbElement = doc.createElement("Database");
            root.appendChild(dbElement);

            IDatabase database = dbController.getDatabase();
            Tables tables = database.getTables();

            Element tablesElement = doc.createElement("Tables");
            dbElement.appendChild(tablesElement);

            for (int i = 0; i < tables.size(); i++) {
                ITable table = tables.get(i);

                Element tableElement = doc.createElement("Table");
                tableElement.setAttribute("name", safeString(table.getName()));
                tableElement.setAttribute("alias", safeString(table.getAlias()));

                // Check if it's a command table (custom SQL)
                if (table instanceof ICommandTable) {
                    ICommandTable cmdTable = (ICommandTable) table;
                    tableElement.setAttribute("type", "Command");

                    Element sqlElement = doc.createElement("CommandText");
                    sqlElement.setTextContent(safeString(cmdTable.getCommandText()));
                    tableElement.appendChild(sqlElement);
                } else {
                    tableElement.setAttribute("type", "Table");
                }

                // Connection info
                IConnectionInfo connInfo = table.getConnectionInfo();
                if (connInfo != null) {
                    Element connElement = doc.createElement("ConnectionInfo");

                    PropertyBag attributes = connInfo.getAttributes();
                    if (attributes != null) {
                        connElement.setAttribute("serverName",
                            safeString((String) attributes.get("QE_ServerDescription")));
                        connElement.setAttribute("databaseName",
                            safeString((String) attributes.get("QE_DatabaseName")));
                    }

                    tableElement.appendChild(connElement);
                }

                // Fields in the table
                extractTableFields(doc, tableElement, table);

                tablesElement.appendChild(tableElement);
            }

            // Table links (joins)
            extractTableLinks(doc, dbElement, database);

        } catch (Exception e) {
            addErrorElement(doc, root, "Database", e);
        }
    }

    /**
     * Extract fields from a table.
     */
    private void extractTableFields(Document doc, Element tableElement, ITable table) {
        try {
            Element fieldsElement = doc.createElement("Fields");
            tableElement.appendChild(fieldsElement);

            Fields fields = table.getDataFields();
            for (int i = 0; i < fields.size(); i++) {
                IField field = fields.get(i);

                Element fieldElement = doc.createElement("Field");
                fieldElement.setAttribute("name", safeString(field.getName()));
                fieldElement.setAttribute("headingText", safeString(field.getHeadingText()));

                FieldValueType valueType = field.getType();
                if (valueType != null) {
                    fieldElement.setAttribute("valueType", valueType.toString());
                }

                fieldsElement.appendChild(fieldElement);
            }
        } catch (Exception e) {
            addErrorElement(doc, tableElement, "Fields", e);
        }
    }

    /**
     * Extract table links (joins).
     */
    private void extractTableLinks(Document doc, Element dbElement, IDatabase database) {
        try {
            Element linksElement = doc.createElement("TableLinks");
            dbElement.appendChild(linksElement);

            TableLinks links = database.getTableLinks();
            for (int i = 0; i < links.size(); i++) {
                ITableLink link = links.get(i);

                Element linkElement = doc.createElement("TableLink");
                linkElement.setAttribute("sourceTable", safeString(link.getSourceTable().getName()));
                linkElement.setAttribute("targetTable", safeString(link.getTargetTable().getName()));

                // Join type
                TableLinkType linkType = link.getJoinType();
                if (linkType != null) {
                    linkElement.setAttribute("joinType", linkType.toString());
                }

                // Link fields
                TableLinkFields sourceFields = link.getSourceFields();
                TableLinkFields targetFields = link.getTargetFields();

                for (int j = 0; j < sourceFields.size(); j++) {
                    Element linkFieldElement = doc.createElement("LinkField");
                    linkFieldElement.setAttribute("sourceField",
                        safeString(sourceFields.get(j).getName()));
                    linkFieldElement.setAttribute("targetField",
                        safeString(targetFields.get(j).getName()));
                    linkElement.appendChild(linkFieldElement);
                }

                linksElement.appendChild(linkElement);
            }
        } catch (Exception e) {
            addErrorElement(doc, dbElement, "TableLinks", e);
        }
    }

    /**
     * Extract report definition (layout).
     */
    private void extractReportDefinition(Document doc, Element root,
            ReportDefController reportDefController, ReportClientDocument clientDoc) {
        try {
            Element layoutElement = doc.createElement("ReportDefinition");
            root.appendChild(layoutElement);

            IReportDocument reportDoc = clientDoc.getReportDocument();

            // Page options
            extractPageOptions(doc, layoutElement, reportDoc);

            // Areas and sections
            Areas areas = reportDoc.getReportDefController().getReportDefinition().getAreas();
            extractAreas(doc, layoutElement, areas);

        } catch (Exception e) {
            addErrorElement(doc, root, "ReportDefinition", e);
        }
    }

    /**
     * Extract page options.
     */
    private void extractPageOptions(Document doc, Element parent, IReportDocument reportDoc) {
        try {
            Element pageElement = doc.createElement("PageOptions");
            parent.appendChild(pageElement);

            // Note: Page options access may vary by SDK version
            // Add what's available

        } catch (Exception e) {
            // Page options not accessible, skip
        }
    }

    /**
     * Extract areas (report sections).
     */
    private void extractAreas(Document doc, Element parent, Areas areas) {
        try {
            Element areasElement = doc.createElement("Areas");
            parent.appendChild(areasElement);

            for (int i = 0; i < areas.size(); i++) {
                IArea area = areas.get(i);

                Element areaElement = doc.createElement("Area");
                areaElement.setAttribute("name", safeString(area.getName()));

                AreaKind kind = area.getKind();
                if (kind != null) {
                    areaElement.setAttribute("kind", kind.toString());
                }

                // Sections within the area
                Sections sections = area.getSections();
                for (int j = 0; j < sections.size(); j++) {
                    ISection section = sections.get(j);

                    Element sectionElement = doc.createElement("Section");
                    sectionElement.setAttribute("name", safeString(section.getName()));
                    sectionElement.setAttribute("height", String.valueOf(section.getHeight()));
                    sectionElement.setAttribute("suppress",
                        String.valueOf(section.getSuppressed()));

                    // Report objects in section
                    extractReportObjects(doc, sectionElement, section);

                    areaElement.appendChild(sectionElement);
                }

                areasElement.appendChild(areaElement);
            }
        } catch (Exception e) {
            addErrorElement(doc, parent, "Areas", e);
        }
    }

    /**
     * Extract report objects (fields, text, etc.).
     */
    private void extractReportObjects(Document doc, Element sectionElement, ISection section) {
        try {
            Element objectsElement = doc.createElement("ReportObjects");
            sectionElement.appendChild(objectsElement);

            ReportObjects objects = section.getReportObjects();
            for (int i = 0; i < objects.size(); i++) {
                IReportObject obj = objects.get(i);

                Element objElement = doc.createElement("ReportObject");
                objElement.setAttribute("name", safeString(obj.getName()));
                objElement.setAttribute("kind", obj.getKind().toString());

                // Position and size
                objElement.setAttribute("left", String.valueOf(obj.getLeft()));
                objElement.setAttribute("top", String.valueOf(obj.getTop()));
                objElement.setAttribute("width", String.valueOf(obj.getWidth()));
                objElement.setAttribute("height", String.valueOf(obj.getHeight()));

                // Suppression
                objElement.setAttribute("suppress",
                    String.valueOf(obj.getObjectFormat().getSuppressed()));

                // Type-specific handling
                if (obj instanceof IFieldObject) {
                    IFieldObject fieldObj = (IFieldObject) obj;
                    objElement.setAttribute("type", "Field");

                    IFieldDefinition fieldDef = fieldObj.getDataSource();
                    if (fieldDef != null) {
                        objElement.setAttribute("dataSource",
                            safeString(fieldDef.getFormulaForm()));
                    }

                } else if (obj instanceof ITextObject) {
                    ITextObject textObj = (ITextObject) obj;
                    objElement.setAttribute("type", "Text");

                    Paragraphs paragraphs = textObj.getParagraphs();
                    StringBuilder textContent = new StringBuilder();
                    for (int p = 0; p < paragraphs.size(); p++) {
                        IParagraph para = paragraphs.get(p);
                        ParagraphElements elements = para.getParagraphElements();
                        for (int e = 0; e < elements.size(); e++) {
                            IParagraphElement pe = elements.get(e);
                            if (pe instanceof IParagraphTextElement) {
                                textContent.append(((IParagraphTextElement) pe).getText());
                            }
                        }
                    }

                    Element textElement = doc.createElement("Text");
                    textElement.setTextContent(textContent.toString());
                    objElement.appendChild(textElement);

                } else if (obj instanceof ISubreportObject) {
                    objElement.setAttribute("type", "Subreport");
                    ISubreportObject subObj = (ISubreportObject) obj;
                    objElement.setAttribute("subreportName",
                        safeString(subObj.getSubreportName()));
                }

                objectsElement.appendChild(objElement);
            }
        } catch (Exception e) {
            addErrorElement(doc, sectionElement, "ReportObjects", e);
        }
    }

    /**
     * Extract subreports.
     */
    private void extractSubreports(Document doc, Element root, SubreportController subreportController) {
        try {
            Element subreportsElement = doc.createElement("Subreports");
            root.appendChild(subreportsElement);

            IStrings subreportNames = subreportController.getSubreportNames();

            for (int i = 0; i < subreportNames.size(); i++) {
                String name = subreportNames.get(i);

                Element subreportElement = doc.createElement("Subreport");
                subreportElement.setAttribute("name", safeString(name));

                // Get subreport links
                try {
                    SubreportLinks links = subreportController.getSubreportLinks(name);
                    for (int j = 0; j < links.size(); j++) {
                        ISubreportLink link = links.get(j);

                        Element linkElement = doc.createElement("SubreportLink");
                        linkElement.setAttribute("mainReportField",
                            safeString(link.getMainReportFieldName()));
                        linkElement.setAttribute("subreportParameter",
                            safeString(link.getSubreportParameterFieldName()));
                        subreportElement.appendChild(linkElement);
                    }
                } catch (Exception e) {
                    // Links not accessible
                }

                subreportsElement.appendChild(subreportElement);
            }
        } catch (Exception e) {
            addErrorElement(doc, root, "Subreports", e);
        }
    }

    /**
     * Write XML document to file.
     */
    private void writeXmlToFile(Document doc, String outputPath) throws Exception {
        TransformerFactory transformerFactory = TransformerFactory.newInstance();
        Transformer transformer = transformerFactory.newTransformer();
        transformer.setOutputProperty(OutputKeys.INDENT, "yes");
        transformer.setOutputProperty("{http://xml.apache.org/xslt}indent-amount", "2");
        transformer.setOutputProperty(OutputKeys.ENCODING, "UTF-8");

        DOMSource source = new DOMSource(doc);
        StreamResult result = new StreamResult(new File(outputPath));
        transformer.transform(source, result);
    }

    /**
     * Add error element to XML.
     */
    private void addErrorElement(Document doc, Element parent, String context, Exception e) {
        Element errorElement = doc.createElement("Error");
        errorElement.setAttribute("context", context);
        errorElement.setAttribute("message", safeString(e.getMessage()));

        // Stack trace
        StringWriter sw = new StringWriter();
        e.printStackTrace(new PrintWriter(sw));
        Element stackElement = doc.createElement("StackTrace");
        stackElement.setTextContent(sw.toString());
        errorElement.appendChild(stackElement);

        parent.appendChild(errorElement);
    }

    /**
     * Safe string conversion (handle nulls).
     */
    private String safeString(Object obj) {
        return obj != null ? obj.toString() : "";
    }
}
