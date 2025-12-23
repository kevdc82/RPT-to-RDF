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

// Crystal Reports SDK - use crystaldecisions (not crystaldecisions12) for local RPT file access
import com.crystaldecisions.sdk.occa.report.application.ReportClientDocument;
import com.crystaldecisions.sdk.occa.report.application.OpenReportOptions;
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

            if (args[0].equals("--verbose")) {
                extractor.verbose = true;
                String[] newArgs = new String[args.length - 1];
                System.arraycopy(args, 1, newArgs, 0, args.length - 1);
                args = newArgs;
            }

            if (args.length == 0) {
                printUsage();
                System.exit(1);
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
        System.out.println("  --verbose          Show detailed error messages");
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

        // Get both absolute path and just the filename
        String absolutePath = inputFile.getAbsolutePath();
        String fileName = inputFile.getName();
        File parentDir = inputFile.getParentFile();

        if (outputPath == null) {
            outputPath = absolutePath.replaceAll("(?i)\\.rpt$", ".xml");
        }

        System.out.println("Processing: " + absolutePath);

        ReportClientDocument clientDoc = new ReportClientDocument();

        try {
            // Configure to use in-process connection (required for local file access)
            clientDoc.setReportAppServer(ReportClientDocument.inprocConnectionString);

            // Try multiple approaches to open the report
            // Note: Crystal Reports SDK resolves paths relative to the JAR file location
            // The reportLocation tag in CRConfig.xml specifies where to find reports
            Exception lastException = null;
            boolean opened = false;

            // Approach 1: Try filename only (when reportLocation is set in CRConfig.xml)
            if (!opened) {
                try {
                    System.out.println("  Trying: filename only (" + fileName + ")");
                    clientDoc.open(fileName, OpenReportOptions._openAsReadOnly);
                    opened = true;
                    System.out.println("  Success with filename only");
                } catch (Exception e) {
                    lastException = e;
                    System.out.println("  Failed: " + e.getMessage());
                }
            }

            // Approach 2: Try static openReport(File) method
            if (!opened) {
                try {
                    System.out.println("  Trying: static openReport(File)");
                    clientDoc = ReportClientDocument.openReport(inputFile);
                    opened = true;
                    System.out.println("  Success with static openReport(File)");
                } catch (Exception e) {
                    lastException = e;
                    System.out.println("  Failed: " + e.getMessage());
                }
            }

            // Approach 3: Try absolute path
            if (!opened) {
                try {
                    System.out.println("  Trying: absolute path (" + absolutePath + ")");
                    clientDoc = new ReportClientDocument();
                    clientDoc.setReportAppServer(ReportClientDocument.inprocConnectionString);
                    clientDoc.open(absolutePath, OpenReportOptions._openAsReadOnly);
                    opened = true;
                    System.out.println("  Success with absolute path");
                } catch (Exception e) {
                    lastException = e;
                    System.out.println("  Failed: " + e.getMessage());
                }
            }

            // Approach 4: Try with integer flag 0 instead of OpenReportOptions
            if (!opened) {
                try {
                    System.out.println("  Trying: absolute path with flag 0");
                    clientDoc = new ReportClientDocument();
                    clientDoc.setReportAppServer(ReportClientDocument.inprocConnectionString);
                    clientDoc.open(absolutePath, 0);
                    opened = true;
                    System.out.println("  Success with flag 0");
                } catch (Exception e) {
                    lastException = e;
                    System.out.println("  Failed: " + e.getMessage());
                }
            }

            if (!opened) {
                throw lastException != null ? lastException : new Exception("Failed to open report");
            }

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
        extractReportDefinition(doc, root, reportDefController);

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
                try {
                    IFormulaField formula = (IFormulaField) formulaFields.get(i);

                    Element formulaElement = doc.createElement("FormulaField");
                    formulaElement.setAttribute("name", safeString(formula.getName()));
                    formulaElement.setAttribute("headingText", safeString(formula.getHeadingText()));

                    // Formula text
                    Element textElement = doc.createElement("Text");
                    textElement.setTextContent(safeString(formula.getText()));
                    formulaElement.appendChild(textElement);

                    // Value type
                    try {
                        FieldValueType valueType = formula.getType();
                        if (valueType != null) {
                            formulaElement.setAttribute("valueType", valueType.toString());
                        }
                    } catch (Exception e) {
                        // Ignore
                    }

                    formulasElement.appendChild(formulaElement);
                } catch (Exception e) {
                    // Skip this formula
                }
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
                try {
                    IParameterField param = (IParameterField) paramFields.get(i);

                    Element paramElement = doc.createElement("ParameterField");
                    paramElement.setAttribute("name", safeString(param.getName()));

                    // Report name
                    try {
                        paramElement.setAttribute("reportName", safeString(param.getReportName()));
                    } catch (Exception e) {
                        // Ignore
                    }

                    // Value type
                    try {
                        FieldValueType valueType = param.getType();
                        if (valueType != null) {
                            paramElement.setAttribute("valueType", valueType.toString());
                        }
                    } catch (Exception e) {
                        // Ignore
                    }

                    // Allow null
                    try {
                        paramElement.setAttribute("allowNullValue", String.valueOf(param.getAllowNullValue()));
                    } catch (Exception e) {
                        // Ignore
                    }

                    paramsElement.appendChild(paramElement);
                } catch (Exception e) {
                    // Skip this parameter
                }
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
                try {
                    IGroup group = (IGroup) groups.get(i);

                    Element groupElement = doc.createElement("Group");

                    // Condition field
                    try {
                        IField condField = group.getConditionField();
                        if (condField != null) {
                            groupElement.setAttribute("conditionFieldName", safeString(condField.getName()));
                        }
                    } catch (Exception e) {
                        // Ignore
                    }

                    groupsElement.appendChild(groupElement);
                } catch (Exception e) {
                    // Skip this group
                }
            }
        } catch (Exception e) {
            addErrorElement(doc, parent, "Groups", e);
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
                try {
                    ISummaryField summary = (ISummaryField) summaryFields.get(i);

                    Element summaryElement = doc.createElement("SummaryField");
                    summaryElement.setAttribute("name", safeString(summary.getName()));

                    // Operation
                    try {
                        SummaryOperation operation = summary.getOperation();
                        if (operation != null) {
                            summaryElement.setAttribute("operation", operation.toString());
                        }
                    } catch (Exception e) {
                        // Ignore
                    }

                    // Summarized field
                    try {
                        IField summarizedField = summary.getSummarizedField();
                        if (summarizedField != null) {
                            summaryElement.setAttribute("summarizedField", safeString(summarizedField.getName()));
                        }
                    } catch (Exception e) {
                        // Ignore
                    }

                    summariesElement.appendChild(summaryElement);
                } catch (Exception e) {
                    // Skip this summary
                }
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
                try {
                    IRunningTotalField rt = (IRunningTotalField) rtFields.get(i);

                    Element rtElement = doc.createElement("RunningTotalField");
                    rtElement.setAttribute("name", safeString(rt.getName()));

                    // Operation
                    try {
                        SummaryOperation operation = rt.getOperation();
                        if (operation != null) {
                            rtElement.setAttribute("operation", operation.toString());
                        }
                    } catch (Exception e) {
                        // Ignore
                    }

                    runningTotalsElement.appendChild(rtElement);
                } catch (Exception e) {
                    // Skip this running total
                }
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
                try {
                    ITable table = (ITable) tables.get(i);

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
                    try {
                        IConnectionInfo connInfo = table.getConnectionInfo();
                        if (connInfo != null) {
                            Element connElement = doc.createElement("ConnectionInfo");

                            try {
                                PropertyBag attributes = connInfo.getAttributes();
                                if (attributes != null) {
                                    Object server = attributes.get("QE_ServerDescription");
                                    Object dbName = attributes.get("QE_DatabaseName");
                                    if (server != null) connElement.setAttribute("serverName", server.toString());
                                    if (dbName != null) connElement.setAttribute("databaseName", dbName.toString());
                                }
                            } catch (Exception e) {
                                // Ignore
                            }

                            tableElement.appendChild(connElement);
                        }
                    } catch (Exception e) {
                        // Ignore
                    }

                    // Fields in the table
                    extractTableFields(doc, tableElement, table);

                    tablesElement.appendChild(tableElement);
                } catch (Exception e) {
                    // Skip this table
                }
            }

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
                try {
                    Object fieldObj = fields.get(i);
                    if (fieldObj instanceof IField) {
                        IField field = (IField) fieldObj;

                        Element fieldElement = doc.createElement("Field");
                        fieldElement.setAttribute("name", safeString(field.getName()));
                        fieldElement.setAttribute("headingText", safeString(field.getHeadingText()));

                        try {
                            FieldValueType valueType = field.getType();
                            if (valueType != null) {
                                fieldElement.setAttribute("valueType", valueType.toString());
                            }
                        } catch (Exception e) {
                            // Ignore
                        }

                        fieldsElement.appendChild(fieldElement);
                    }
                } catch (Exception e) {
                    // Skip this field
                }
            }
        } catch (Exception e) {
            addErrorElement(doc, tableElement, "Fields", e);
        }
    }

    /**
     * Extract report definition (layout).
     */
    private void extractReportDefinition(Document doc, Element root, ReportDefController reportDefController) {
        try {
            Element layoutElement = doc.createElement("ReportDefinition");
            root.appendChild(layoutElement);

            // Get report definition
            IReportDefinition reportDef = reportDefController.getReportDefinition();

            // Areas and sections
            Areas areas = reportDef.getAreas();
            extractAreas(doc, layoutElement, areas);

        } catch (Exception e) {
            addErrorElement(doc, root, "ReportDefinition", e);
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
                try {
                    IArea area = (IArea) areas.get(i);

                    Element areaElement = doc.createElement("Area");
                    areaElement.setAttribute("name", safeString(area.getName()));

                    try {
                        AreaSectionKind kind = area.getKind();
                        if (kind != null) {
                            areaElement.setAttribute("kind", kind.toString());
                        }
                    } catch (Exception e) {
                        // Ignore
                    }

                    // Sections within the area
                    try {
                        Sections sections = area.getSections();
                        for (int j = 0; j < sections.size(); j++) {
                            try {
                                ISection section = (ISection) sections.get(j);

                                Element sectionElement = doc.createElement("Section");
                                sectionElement.setAttribute("name", safeString(section.getName()));

                                try {
                                    sectionElement.setAttribute("height", String.valueOf(section.getHeight()));
                                } catch (Exception e) {
                                    // Ignore
                                }

                                // Report objects in section
                                extractReportObjects(doc, sectionElement, section);

                                areaElement.appendChild(sectionElement);
                            } catch (Exception e) {
                                // Skip this section
                            }
                        }
                    } catch (Exception e) {
                        // Ignore sections
                    }

                    areasElement.appendChild(areaElement);
                } catch (Exception e) {
                    // Skip this area
                }
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
                try {
                    IReportObject obj = (IReportObject) objects.get(i);

                    Element objElement = doc.createElement("ReportObject");
                    objElement.setAttribute("name", safeString(obj.getName()));

                    try {
                        objElement.setAttribute("kind", obj.getKind().toString());
                    } catch (Exception e) {
                        // Ignore
                    }

                    // Position and size
                    try {
                        objElement.setAttribute("left", String.valueOf(obj.getLeft()));
                        objElement.setAttribute("top", String.valueOf(obj.getTop()));
                        objElement.setAttribute("width", String.valueOf(obj.getWidth()));
                        objElement.setAttribute("height", String.valueOf(obj.getHeight()));
                    } catch (Exception e) {
                        // Ignore
                    }

                    // Type-specific handling
                    if (obj instanceof IFieldObject) {
                        IFieldObject fieldObj = (IFieldObject) obj;
                        objElement.setAttribute("type", "Field");

                        try {
                            // getDataSource() returns Object - try to get formula form
                            Object dataSource = fieldObj.getDataSource();
                            if (dataSource != null) {
                                // Try to cast to IField which has getFormulaForm()
                                if (dataSource instanceof IField) {
                                    IField fieldDef = (IField) dataSource;
                                    objElement.setAttribute("dataSource", safeString(fieldDef.getFormulaForm()));
                                } else {
                                    // Fallback to toString
                                    objElement.setAttribute("dataSource", safeString(dataSource.toString()));
                                }
                            }
                        } catch (Exception e) {
                            // Ignore
                        }

                    } else if (obj instanceof ITextObject) {
                        ITextObject textObj = (ITextObject) obj;
                        objElement.setAttribute("type", "Text");

                        try {
                            Paragraphs paragraphs = textObj.getParagraphs();
                            StringBuilder textContent = new StringBuilder();
                            for (int p = 0; p < paragraphs.size(); p++) {
                                IParagraph para = (IParagraph) paragraphs.get(p);
                                ParagraphElements elements = para.getParagraphElements();
                                for (int pe = 0; pe < elements.size(); pe++) {
                                    IParagraphElement elem = (IParagraphElement) elements.get(pe);
                                    if (elem instanceof IParagraphTextElement) {
                                        textContent.append(((IParagraphTextElement) elem).getText());
                                    }
                                }
                            }

                            Element textElement = doc.createElement("Text");
                            textElement.setTextContent(textContent.toString());
                            objElement.appendChild(textElement);
                        } catch (Exception e) {
                            // Ignore
                        }

                    } else if (obj instanceof ISubreportObject) {
                        objElement.setAttribute("type", "Subreport");
                        ISubreportObject subObj = (ISubreportObject) obj;
                        try {
                            objElement.setAttribute("subreportName", safeString(subObj.getSubreportName()));
                        } catch (Exception e) {
                            // Ignore
                        }
                    }

                    objectsElement.appendChild(objElement);
                } catch (Exception e) {
                    // Skip this object
                }
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
                try {
                    // IStrings.get() may return String or Object depending on SDK version
                    Object nameObj = subreportNames.get(i);
                    String name = nameObj != null ? nameObj.toString() : "";

                    Element subreportElement = doc.createElement("Subreport");
                    subreportElement.setAttribute("name", safeString(name));

                    // Get subreport links
                    try {
                        SubreportLinks links = subreportController.getSubreportLinks(name);
                        for (int j = 0; j < links.size(); j++) {
                            try {
                                ISubreportLink link = (ISubreportLink) links.get(j);

                                Element linkElement = doc.createElement("SubreportLink");
                                linkElement.setAttribute("mainReportField",
                                    safeString(link.getMainReportFieldName()));

                                // Try to get subreport parameter name via reflection
                                // since getLinkedParameterField() may not exist in this SDK version
                                try {
                                    java.lang.reflect.Method method = link.getClass().getMethod("getLinkedParameterField");
                                    Object paramField = method.invoke(link);
                                    if (paramField != null) {
                                        // Try to get name from the parameter field
                                        java.lang.reflect.Method getName = paramField.getClass().getMethod("getName");
                                        Object paramName = getName.invoke(paramField);
                                        if (paramName != null) {
                                            linkElement.setAttribute("subreportParameter",
                                                safeString(paramName.toString()));
                                        }
                                    }
                                } catch (NoSuchMethodException nsme) {
                                    // Method doesn't exist in this SDK version, try alternative
                                    try {
                                        java.lang.reflect.Method method = link.getClass().getMethod("getSubreportParameterFieldName");
                                        Object paramName = method.invoke(link);
                                        if (paramName != null) {
                                            linkElement.setAttribute("subreportParameter",
                                                safeString(paramName.toString()));
                                        }
                                    } catch (Exception ex) {
                                        // Ignore - method not available
                                    }
                                } catch (Exception e) {
                                    // Ignore
                                }

                                subreportElement.appendChild(linkElement);
                            } catch (Exception e) {
                                // Skip this link
                            }
                        }
                    } catch (Exception e) {
                        // Links not accessible
                    }

                    subreportsElement.appendChild(subreportElement);
                } catch (Exception e) {
                    // Skip this subreport
                }
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

        if (verbose) {
            // Stack trace
            StringWriter sw = new StringWriter();
            e.printStackTrace(new PrintWriter(sw));
            Element stackElement = doc.createElement("StackTrace");
            stackElement.setTextContent(sw.toString());
            errorElement.appendChild(stackElement);
        }

        parent.appendChild(errorElement);
    }

    /**
     * Safe string conversion (handle nulls).
     */
    private String safeString(Object obj) {
        return obj != null ? obj.toString() : "";
    }
}
